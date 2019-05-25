from ntu.votes.candidate import Candidate
from ntu.votes.utility import Utility, BordaUtility

__doc__ = """
Define different types of voters

There are general voters, lazy voters, and Truthful voters.
"""


class Voter:

    position: int = None
    profile: list = None
    utility: Utility = None

    def __init__(self, position: int, utility: Utility = BordaUtility):
        self.position = position
        self.utility = utility

    def __repr__(self):
        return f"{self.__class__.__name__}({self.position})\t{self.profile}"

    # def build_profile(self, candidates: list = None, profile: ProfilePreference = SinglePeakedProfilePreference()):
    def build_profile(self, candidates: list = None, profile=None):
        self.profile = profile.build_preference_profile(self, candidates)

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

    class UpdateEvent:
        # def __init__(self, source: Voter = None, frm: Candidate = None, to: Candidate = None):
        def __init__(self, source=None, frm: Candidate = None, to: Candidate = None):
            self.source = source
            self.frm = frm
            self.to = to

        def __repr__(self):
            return str((self.source, self.frm, self.to))

    def vote(self, current_state: list) -> UpdateEvent:
        if self.profile is None:
            raise RuntimeError("Please create a profile first")


class GeneralVoter(Voter):

    def vote(self, current_state: list) -> Voter.UpdateEvent:
        super().vote(current_state)
        return


class TruthfulVoter(Voter):

    def vote(self, current_state: list) -> Voter.UpdateEvent:
        super().vote(current_state)
        return


class LazyVoter(Voter):
    abstain: bool = False

    def vote(self, current_state: list) -> Voter.UpdateEvent:
        if self.abstain:
            return current_state
        super().vote(current_state)
        return




class Status:
    __votes__ = {}

    def fillstatus(self, profile):
        votes = {}


######################################

if __name__ == '__main__':
    g = Voter.make_general_voter(2)
    print(g)
    t = Voter.make_truthful_voter(2)
    print(t)
    lzy = Voter.make_lazy_voter(2)
    print(lzy)

