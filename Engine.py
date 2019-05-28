import argparse
import sys

from ntu.votes import utility
from ntu.votes.candidate import *
from ntu.votes.profilepreference import *
from ntu.votes.tiebreaking import *
from ntu.votes.utility import ExpoUtility, UtilityTypes
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

    tiebreakingrule = {
        'LexicographicTieBreakingRule': LexicographicTieBreakingRule(),
        'RandomTieBreakingRule': RandomTieBreakingRule(),
    }.get(args.tiebreakingrule, None)

    # print(utility, preference, tiebreakingrule)

    for n_candidates in range(5, 8):
        # number of n_candidates <= n_voters <= 12 #TODO verify this with L & Z
        for n_voters in range(n_candidates, 13):
            if n_voters % 2 == 1:
                continue
            all_candidates = generate_candidates(n_candidates)
            print(all_candidates)
            all_voters = generate_voters(n_voters, args.voters, utility)
            print(all_voters)


def generate_voters(n_voters, voter_type, utility):
    all_voters = []
    for i in range(n_voters):
        v: Voter = Voter.make_voter(voter_type, i+1, utility)
        all_voters.append(v)
    return all_voters


def generate_candidates(n_candidates):
    all_candidates = []
    for i in range(n_candidates):
        c: Candidate = Candidate(chr(b'A'[0]+i), i+1)
        all_candidates.append(c)
    return all_candidates


# --------------------------
if __name__ == '__main__':
    main()

