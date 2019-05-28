from enum import Enum, auto

from ntu.votes.candidate import *
from ntu.votes.tiebreaking import TieBreakingRule


class Utility(object):

    def score(self, voter_profile: list, candidate: Candidate) -> int:
        raise NotImplementedError

    def __call__(self, voter_profile: list, candidate: Candidate) -> int:
        return self.score(voter_profile, candidate)

    def total_utility(self, user_profile: list, potential_winners: list, tiebreakingrule: TieBreakingRule) -> float:
        total = 0.0
        for candidate in potential_winners:
            total += (self.score(user_profile, candidate)
                    * tiebreakingrule.winning_probability(potential_winners, candidate))
        return total

    @classmethod
    def make_utility(cls, utility_type: str) -> 'Utility':
        new = {
            UtilityTypes.BordaUtility.name: cls.__new__(BordaUtility),
            UtilityTypes.ExpoUtility.name: cls.__new__(ExpoUtility),
        }.get(utility_type, None)
        cls.__init__(new)
        return new


class BordaUtility(Utility):

    def score(self, voter_profile: list, candidate: Candidate) -> int:
        try:
            return len(voter_profile) - voter_profile.index(candidate) - 1
        except ValueError:
            raise ValueError(f"Candidate {candidate} not found")


class ExpoUtility(Utility):

    def __init__(self, base: int = 2, exponent_step: int = 1):
        """If you are going to parameterize this callable, please use the direct constructor, not make_utility().

        :param base:
        :param exponent_step:
        """
        if base:
            self.base = base
        if exponent_step:
            self.exponent_step= exponent_step

    def score(self, voter_profile: list, candidate: Candidate) -> int:
        index = voter_profile.index(candidate)
        if index < 0:
            raise ValueError(f"Candidate {candidate} not found")
        else:
            return self.base ** (self.exponent_step * (len(voter_profile) - index - 1))


class UtilityTypes(Enum):
    BordaUtility = auto()
    ExpoUtility = auto()


if __name__ == '__main__':
    profile = []
    for i in range(10):
        a = Candidate(chr(b'A'[0]+i), i)
        print(a)
        profile.append(a)

    print()
    # utility = BordaUtility()
    utility = Utility.make_utility('BordaUtility')

    print(utility(profile, profile[0]))
    print(utility(profile, profile[-1]))
    print(utility(profile, Candidate('B', 1)))
    # print(utility(profile, Candidate('B', 5)))

    print()
    utility = ExpoUtility()
    # utility = Utility.make_utility('ExpoUtility')

    print(utility.score(profile, profile[0]))
    print(utility.score(profile, profile[-1]))
    print(utility.score(profile, Candidate('B', 1)))
    # print(utility(profile, Candidate('B', 5)))

    print()
    utility = ExpoUtility(3, 2)

    print(utility(profile, profile[0]))
    print(utility(profile, profile[-1]))
    print(utility(profile, Candidate('B', 1)))
    # print(utility(profile, Candidate('B', 5)))

    print()
    utility = ExpoUtility(3)

    print(utility(profile, profile[0]))
    print(utility(profile, profile[-1]))
    print(utility(profile, Candidate('B', 1)))
    # print(utility(profile, Candidate('B', 5)))
