
from ntu.votes.candidate import *


class Utility(object):
    @classmethod
    def score(cls, voter_profile: list, candidate: Candidate) -> int:
        raise NotImplementedError

    @classmethod
    def __call__(cls, voter_profile: list, candidate: Candidate) -> int:
        return cls.score(voter_profile, candidate)


class BordaUtility(Utility):
    @classmethod
    def score(cls, voter_profile: list, candidate: Candidate) -> int:
        try:
            return len(voter_profile) - voter_profile.index(candidate) - 1
        except ValueError:
            raise ValueError(f"Candidate {candidate} not found")


class ExpoUtility(Utility):
    @classmethod
    def score(cls, voter_profile: list, candidate: Candidate) -> int:
        index = voter_profile.index(candidate)
        if index < 0:
            raise ValueError(f"Candidate {candidate} not found")
        else:
            return  2 ** (len(voter_profile) - index -1)


if __name__ == '__main__':
    profile = []
    for i in range(10):
        a = Candidate(chr(b'A'[0]+i), i)
        print(a)
        profile.append(a)

    print()
    utility = BordaUtility()

    # print(utility.score(profile, profile[0]))
    # print(utility.score(profile, profile[-1]))
    # print(utility.score(profile, Candidate('B', 1)))
    # # print(utility.score(profile, Candidate('B', 5)))
    print(utility(profile, profile[0]))
    print(utility(profile, profile[-1]))
    print(utility(profile, Candidate('B', 1)))
    # print(utility(profile, Candidate('B', 5)))

    print()
    utility = ExpoUtility()

    print(utility.score(profile, profile[0]))
    print(utility.score(profile, profile[-1]))
    print(utility.score(profile, Candidate('B', 1)))
    # print(utility.score(profile, Candidate('B', 5)))
