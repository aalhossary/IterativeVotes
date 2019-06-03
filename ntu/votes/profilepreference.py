import operator
import random
from random import Random

from ntu.votes.candidate import Candidate
from ntu.votes.voter import Voter


#################################################


class ProfilePreference:

    @classmethod
    def build_profile(cls, voter: Voter, candidates: list) -> list:
        raise NotImplementedError


class SinglePeakedProfilePreference(ProfilePreference):

    @classmethod
    def build_profile(cls, voter: Voter, candidates: list) -> list:
        distances = [(candidate.distance_to(voter.position), candidate) for candidate in candidates]
        # print(distances)
        '''TODO shall it be itemgetter(0,1) or itemgetter(0) only?
        i.e. after ordering based on the distance to voter, shall follow the original order or include lexicographical 
        ordering of the candidates as well? '''
        distances.sort(key=operator.itemgetter(0, 1))
        # print(distances)
        return [c for d, c in distances]


class GeneralProfilePreference(ProfilePreference):
    rand = None

    def __init__(self, rand: Random) -> None:
        super().__init__()
        self.__class__.rand = rand

    @classmethod
    def build_profile(cls, voter: Voter, candidates: list) -> list:
        temp = candidates.copy()
        cls.rand.shuffle(temp)
        return temp


#################################################

if __name__ == '__main__':
    cc = [
        Candidate('B', 2),
        Candidate('B', 1),
        Candidate('A', 1),
        Candidate('A', 2),
        Candidate('C', 3),
        Candidate('D', 4)
    ]
    # print(sorted(cc), key=LexicographicTieBreakingRule.sort_key))
    print(sorted(cc))

    # ------------------------
    preference: ProfilePreference = SinglePeakedProfilePreference()
    print(preference.build_profile(Voter(2), cc))

    preference = GeneralProfilePreference(Random())
    print(preference.build_profile(Voter(2), cc))
    print(preference.build_profile(Voter(2), cc))

