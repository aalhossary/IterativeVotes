import argparse
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

    args = parser.parse_args()

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
        'RandomTieBreakingRule': RandomTieBreakingRule(),
    }.get(args.tiebreakingrule, None)

    print(utility, preference, tie_breaking_rule)

    for n_candidates in range(5, 8):
        # number of n_candidates <= n_voters <= 12 #TODO verify this with L & Z
        for n_voters in range(n_candidates, 13):
            if n_voters % 2 == 1:
                continue

            print(f"\n------------ voters = {n_voters}, Candidates = {n_candidates}-------------------")
            all_candidates = generate_candidates(n_candidates)
            # print(all_candidates)
            all_voters = generate_voters(n_voters, args.voters, n_candidates, utility)
            # print(all_voters)

            # voters build their preferences
            for voter in all_voters:
                voter.build_profile(all_candidates, preference)
            # collective profile
            profile = [voter.getprofile() for voter in all_voters]
            initial_status = Status.from_profile(profile)

            # TODO from here, initialize every thing in every run (fork a function ?)
            active_voters_indices = [i for i in range(len(all_voters))]
            # now for the initial status
            current_status = initial_status.copy()
            print(current_status, "Initial state")
            step = 0
            while step < len(all_voters) * len(all_candidates):
                # pick a voter from ACTIVE voters
                index = random.choice(active_voters_indices)
                voter = all_voters[index]
                # ask him to vote
                response = voter.vote(current_status, tie_breaking_rule)
                print(current_status, response, end='\t')
                # evaluate the status
                if response.to is None:
                    if isinstance(voter, LazyVoter):
                        active_voters_indices.__delitem__(index)
                        if not len(active_voters_indices):
                            # conversed
                            print("Conversion")
                            break
                elif response.frm is response.to:
                    # voter was satisfied
                    pass # TODO shall this happen? if yes, fill it
                else:
                    current_status.votes[response.frm] = current_status.votes[response.frm] - 1
                    current_status.votes[response.to] = current_status.votes[response.to] + 1
                    current_status.in_order()
                    print("<-- enhancement", end='\t')
                # step++
                step += 1
                print()


def generate_voters(n_voters: int, voter_type, positions_range: int, utility):
    all_voters = []
    for i in range(n_voters):
        v: Voter = Voter.make_voter(voter_type, random.randrange(positions_range), utility)
        all_voters.append(v)
    return all_voters


def generate_candidates(n_candidates):
    """We assume that they are (((uniformly))) distributed

    TODO double check this
    :param n_candidates:
    :return:
    """
    all_candidates = []
    for i in range(n_candidates):
        c: Candidate = Candidate(chr(b'A'[0]+i), i+1)
        all_candidates.append(c)
    return all_candidates


# --------------------------
if __name__ == '__main__':
    main()

