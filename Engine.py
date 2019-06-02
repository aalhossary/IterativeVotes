import argparse
from random import Random
import sys

from ntu.votes import utility
from ntu.votes.candidate import *
from ntu.votes.profilepreference import *
from ntu.votes.tiebreaking import *
from ntu.votes.utility import *
from ntu.votes.voter import *

# =======================
__doc__ = """
•	Number of voters is even and <= 12
•	Number of candidates between 5 and 7
•	Number of repeated runs per preference profile is 50 (random iteration sequences per profile)

"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--candidates", help="number of candidates", default=5)
    parser.add_argument("-v", "--voters", help="type of voters", default='GeneralVoter')
    parser.add_argument("-u", "--utility", help="The utility Function", default= 'BordaUtility')
    parser.add_argument("-p", "--preference", help="ow a voter forms his ballot order",
                        default='SinglePeakedProfilePreference')
    parser.add_argument("-t", "--tiebreakingrule", help="how to behave in cases of draws",
                        default='LexicographicTieBreakingRule')
    parser.add_argument("-s", "--seed", help="initial seed",
                        default=None)  # TODO update

    args = parser.parse_args()

    rand = random.Random(args.seed)

    # if args.candidates:
    #     print("candidates = ", args.candidates)
    # if args.voters:
    #     print("voters = ", args.voters)
    utility = {
        'BordaUtility': BordaUtility(),
        'ExpoUtility': ExpoUtility(),
    }.get(args.utility, None)
    # TODO use ExpoUtility parameters if any

    preference = {
        'SinglePeakedProfilePreference': SinglePeakedProfilePreference(),
        'GeneralProfilePreference': GeneralProfilePreference(),
    }.get(args.preference, None)

    tie_breaking_rule = {
        'LexicographicTieBreakingRule': LexicographicTieBreakingRule(),
        'RandomTieBreakingRule': RandomTieBreakingRule(rand),
    }.get(args.tiebreakingrule, None)

    print(utility, preference, tie_breaking_rule)

    for n_candidates in range(5, 8):
        # number of n_candidates <= n_voters <= 12 #TODO verify this with L & Z
        for n_voters in range(n_candidates, 13):
            if n_voters % 2 == 1:
                continue

            # for voter_types in ['GeneralVoter', ]
            print(f"\n------------ voters = {n_voters}, Candidates = {n_candidates}-------------------")
            all_candidates = generate_candidates(n_candidates, rand)
            # print(all_candidates)
            all_voters = generate_voters(n_voters, args.voters, n_candidates, utility, rand)
            # print(all_voters)

            # voters build their preferences
            for voter in all_voters:
                voter.build_profile(all_candidates, preference)
            # collective profile
            profile = [voter.getprofile() for voter in all_voters]
            initial_status = Status.from_profile(profile)

            for run in range(50):
                scenario = run_simulation(all_candidates, all_voters, initial_status, tie_breaking_rule, rand)


def run_simulation(all_candidates: list, all_voters: list, current_status: Status, tie_breaking_rule: TieBreakingRule,
                   rand: Random) -> list:
    """

    :param tie_breaking_rule:
    :param current_status:
    :param all_voters:
    :param all_candidates:
    :param rand:
    :type rand: Random
    """
    scenario = []
    # only increase
    abstaining_voters_indices = []
    # now for the initial status
    print(current_status, "Initial state")
    scenario.append(current_status.copy())
    step = 0
    max_steps = len(all_voters) * len(all_candidates)
    while step < max_steps:
        # recalculated every step, always decrease
        active_voters_indices = [i for i in range(len(all_voters))]
        if len(current_status.winners) < 2:
            active_voters_indices = [i for i in active_voters_indices
                                     if all_voters[i].most_recent_vote is not current_status.winners[0]]
        else:
            # TODO double check this condition
            active_voters_indices = [i for i in active_voters_indices if tie_breaking_rule.winning_probability(
                current_status.winners, all_voters[i].most_recent_vote) >= 1 / len(current_status.winners)]
        active_voters_indices = [i for i in active_voters_indices if i not in abstaining_voters_indices]

        # Select one voter randomly from Current active_voters_indices list
        while len(active_voters_indices) > 0 and step < max_steps:
            # pick a voter from ACTIVE voters
            index = rand.choice(active_voters_indices)
            voter = all_voters[index]
            # ask him to vote
            response = voter.vote(current_status, tie_breaking_rule)
            scenario.append(response)
            print(current_status, response, end='\t')
            # evaluate the status
            if response.to is None:
                # couldn't enhance
                active_voters_indices.remove(index)
                if isinstance(voter, LazyVoter):
                    abstaining_voters_indices.append(index)
                if not len(active_voters_indices):
                    converged(current_status, scenario)
                    return scenario
            # elif response.frm is response.to:
            #     # voter was satisfied
            #     pass  # Dead case
            else:
                current_status.votes[response.frm] = current_status.votes[response.frm] - 1
                current_status.votes[response.to] = current_status.votes[response.to] + 1
                current_status.in_order()
                print("<-- enhancement", end='\t')
                active_voters_indices.remove(index)
                scenario.append(current_status.copy())
                # return scenario
            step += 1
            print()
        else:
            # no more voters in the list
            converged(current_status, scenario)
            return scenario


def converged(last_status: Status, scenario: list):
    print("Converged")
    print(last_status, "Final state")
    scenario.append(last_status.copy())


def generate_voters(n_voters: int, voter_type, positions_range: int, utility: Utility, rand: Random):
    all_voters = []
    for i in range(n_voters):
        # v: Voter = Voter.make_voter(voter_type, rand.randrange(positions_range), utility)
        v: Voter = Voter.make_voter(voter_type, rand.random(), utility)
        all_voters.append(v)
    return all_voters


def generate_candidates(n_candidates: int, rand: Random):
    all_candidates = []
    for i in range(n_candidates):
        # c: Candidate = Candidate(chr(b'A'[0]+i), i+1)
        c: Candidate = Candidate(chr(b'A'[0]+i), rand.random())
        all_candidates.append(c)
    return all_candidates


# --------------------------
if __name__ == '__main__':
    main()

