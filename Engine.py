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


class Measurements:
    percentage_of_convergence: float
    averageTimeToConvergence: float
    averageSocial_welfare: float
    # How many different stable states we have across all iteration sequences of the same preference profile
    stable_states_sets: set
    winning_sets: set
    percentage_truthful_winner_wins: float
    percentage_winner_is_weak: float

    def __init__(self):
        self.stable_states_sets = set()
        self.winning_sets = set()
        self.percentage_winner_is_weak = -1

    def __str__(self):
        return f"percentage_of_convergence = {self.percentage_of_convergence}\n" \
            f"averageTimeToConvergence = {self.averageTimeToConvergence}\n" \
            f"averageSocial_welfare = {self.averageSocial_welfare}\n" \
            f"stable_states_sets: count = {len(self.stable_states_sets)}, repr = {self.stable_states_sets}\n" \
            f"winning_sets: count = {len(self.winning_sets)}, repr = {self.winning_sets}\n" \
            f"percentage_truthful_winner_wins = {self.percentage_truthful_winner_wins}%\n" \
            f"percentage_winner_is_weak = {self.percentage_winner_is_weak}% [Not yet Implemented]"

def aggregate_alleles(alleles, all_voters, utility: Utility, tiebreakingrule: TieBreakingRule) \
        -> Measurements:
    measurements = Measurements()
    convergence_counter = welfare = truthful_winner_wins_counter = winner_is_weak_counter = 0.0
    steps_before_convergence = []
    for allele in alleles:
        initial_state: Status = allele[0]
        converged: bool = allele[-1]
        final_status = allele[-2]
        # lastAction: UpdateEvent = allele[-3] # not needed
        if converged:
            convergence_counter += 1
            # initial state, final boolean, 2 entries each step
            steps_before_convergence.append((len(allele) - 1 - 1 ) / 2)
            # TODO I assume stable states means converged states. Please verify
            measurements.stable_states_sets.add(tuple(final_status.winners))

        for voter in all_voters:
            welfare += utility.total_utility(voter.profile, final_status.winners, tiebreakingrule)
        if isinstance(tiebreakingrule, RandomTieBreakingRule):
            measurements.winning_sets.add(tuple(final_status.winners))
        elif isinstance(tiebreakingrule, LexicographicTieBreakingRule):
            measurements.winning_sets.add(tuple([tiebreakingrule.get_winner(final_status.winners)]))
        else:
            # TODO find a more approprite exception type
            raise ValueError("Tie breaking rule not known")
        if initial_state.winners == final_status.winners:
            truthful_winner_wins_counter += 1
        # TODO Weak winner
        # if is_winner_weak():
        #     winner_is_weak_counter += 1
    measurements.percentage_of_convergence = convergence_counter * 100.0 / len(steps_before_convergence)
    measurements.averageTimeToConvergence = sum(steps_before_convergence) / len(steps_before_convergence)
    measurements.averageSocial_welfare = welfare / len(alleles)
    measurements.percentage_truthful_winner_wins = truthful_winner_wins_counter * 100 / len(alleles)

    return measurements


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
                        default=None)

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
        'GeneralProfilePreference': GeneralProfilePreference(rand),
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

            alleles = []
            for run in range(50):
                scenario = run_simulation(all_candidates, all_voters, initial_status, tie_breaking_rule, rand)
                alleles.append(scenario)
            measurements = aggregate_alleles(alleles, all_voters, utility, tie_breaking_rule)
            print("-------measurements")
            print(measurements)
            print("-------")


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
                    return converged(current_status, scenario)
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
            step += 1
            print()
        else:
            # no more voters in the list
            return converged(current_status, scenario)
    else:
        return not_converged(current_status, scenario)


def converged(last_status: Status, scenario: list) -> list:
    print("Converged")
    print(last_status, "Final state")
    scenario.append(last_status.copy())
    scenario.append(True)
    return scenario


def not_converged(last_status: Status, scenario: list) -> list:
    print(last_status, "No convergence")
    scenario.append(last_status.copy())
    scenario.append(False)
    return scenario


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

