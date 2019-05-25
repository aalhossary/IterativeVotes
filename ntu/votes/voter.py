import operator

from ntu.votes.candidate import Candidate
# from ntu.votes.profilepreference import SinglePeakedProfilePreference
from ntu.votes.utility import Utility, BordaUtility

__doc__ = """
Define different types of voters

There are general voters, lazy voters, and Truthful voters.
"""


class UpdateEvent:
    """Immutable class"""
    def __init__(self, source: 'Voter' = None, frm: Candidate = None, to: Candidate = None):
        self.source = source
        self.frm = frm
        self.to = to

    def __repr__(self):
        return str((self.source, self.frm, self.to))


class Status:
    __votes__: dict = None
    winners: list = None
    runner_ups: list = None

    @classmethod
    def from_profile(cls, profile: list) -> 'Status':
        votes = [user_profile[0] for user_profile in profile]
        return cls.from_votes(votes)

    @classmethod
    def from_votes(cls, votes: list) -> 'Status':
        new = cls.__new__(Status)
        new.__votes__ = {}
        for candidate in votes:
            new.__votes__[candidate] = new.__votes__.get(candidate, 0) + 1
        ordered = new.in_order()
        return new

    def in_order(self) -> list:
        """Return the votes are a list of frequencies, and cache the top two groups (winners and runner ups)."""
        lst = list(self.__votes__.items())
        """If using Python 3.7, dictionary order is guaranteed preserved"""
        lst.sort(key=operator.itemgetter(1), reverse=True)
        self.cache_top_candidates(lst)
        return lst

    def cache_top_candidates(self, ordered: list):
        top_score = ordered[0][1]
        self.winners = [candidate for (candidate, freq) in ordered if freq == top_score]
        self.runner_ups = [candidate for (candidate, freq) in ordered if freq == top_score - 1]
        # to make it probably faster later, provided that we are using Python 3.7+ or cpython 3.6
        self.__votes__ = dict(ordered)


class Voter:

    position: int = None
    profile: list = None
    utility: Utility = None

    def __init__(self, position: int, utility: Utility = BordaUtility):
        self.position = position
        self.utility = utility

    def __repr__(self):
        return f"{self.__class__.__name__}({self.position})\t{self.profile}"

    # def build_profile(self, candidates: list = None, profile: 'ProfilePreference' = SinglePeakedProfilePreference()):
    def build_profile(self, candidates: list = None, profile=None):
        self.profile = profile.build_profile(self, candidates)

    @classmethod
    def make_general_voter(cls, position: int, utility: Utility = BordaUtility):
        new = cls.__new__(Voter)
        cls.__init__(new, position, utility)
        return new

    @classmethod
    def make_truthful_voter(cls, position: int, utility: Utility = BordaUtility):
        new = cls.__new__(TruthfulVoter)
        cls.__init__(new, position, utility)
        return new

    @classmethod
    def make_lazy_voter(cls, position: int, utility: Utility = BordaUtility):
        new = cls.__new__(LazyVoter)
        cls.__init__(new, position, utility)
        return new

    def get_truthful_vote(self) -> Candidate:
        return self.profile[0]

    def getprofile(self) -> list:
        return self.profile

    def propose_update(self, status: Status) -> UpdateEvent:
        raise NotImplementedError

    def vote(self, current_state: list) -> UpdateEvent:
        if self.profile is None:
            raise RuntimeError("Please create a profile first")
        return None


class GeneralVoter(Voter):

    def vote(self, current_state: list) -> UpdateEvent:
        super().vote(current_state)
        return


class TruthfulVoter(Voter):

    def vote(self, current_state: list) -> UpdateEvent:
        super().vote(current_state)
        return


class LazyVoter(Voter):
    abstain: bool = False

    def vote(self, current_state: list) -> UpdateEvent:
        if self.abstain:
            return UpdateEvent(self)
        super().vote(current_state)
        update = self.propose_update(self, current_state)
        return


######################################
if __name__ == '__main__':
    g = Voter.make_general_voter(2)
    print(g)
    t = Voter.make_truthful_voter(2)
    print(t)
    lzy = Voter.make_lazy_voter(2)
    print(lzy)

    status = Status.from_profile(
        [
            [Candidate('A', 1), Candidate('B', 2), Candidate('C', 3)],
            [Candidate('A', 1), Candidate('B', 2), Candidate('C', 3)],
            [Candidate('E', 5), Candidate('A', 1), Candidate('C', 3)],
            [Candidate('E', 5), Candidate('A', 1), Candidate('C', 3)],
            [Candidate('E', 5), Candidate('A', 1), Candidate('C', 3)],
            [Candidate('D', 4), Candidate('A', 1), Candidate('C', 3)],
            [Candidate('D', 4), Candidate('A', 1), Candidate('C', 3)],
            [Candidate('D', 4), Candidate('A', 1), Candidate('C', 3)],
            [Candidate('B', 2), Candidate('A', 1), Candidate('C', 3)],
            [Candidate('B', 2), Candidate('A', 1), Candidate('C', 3)],
            [Candidate('C', 3), Candidate('A', 1), Candidate('B', 2)],
        ]
    )
    orderedCandidates = status.in_order()
    print(orderedCandidates)
    print(status.winners)
    print(status.runner_ups)


