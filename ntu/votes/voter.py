import operator
from enum import Enum, auto

from ntu.votes.candidate import Candidate
# from ntu.votes.profilepreference import SinglePeakedProfilePreference
from ntu.votes.tiebreaking import TieBreakingRule
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
    votes: dict = None  # contains only the candidates which have at least one vote
    toppers: list = None
    runner_ups: list = None

    @classmethod
    def from_profile(cls, profile: list) -> 'Status':
        votes = [user_profile[0] for user_profile in profile]
        return cls.from_votes(votes, profile[0])

    @classmethod
    def from_votes(cls, votes: list, all_candidates: list) -> 'Status':
        new = cls.__new__(Status)
        new.votes = {candidate: 0 for candidate in all_candidates}  # This 'votes' is a dictionary
        for candidate in votes:  # This 'votes' is a list.
            new.votes[candidate] = new.votes[candidate] + 1
        new.in_order()
        return new

    def in_order(self) -> list:
        """Return the votes as a list of frequencies, and cache the top two groups (toppers and runner ups)."""
        lst = list(self.votes.items())
        """If using Python 3.7, dictionary order is guaranteed to be preserved"""
        lst.sort(key=operator.itemgetter(1), reverse=True)
        self.__cache_top_candidates(lst)
        return lst

    def __cache_top_candidates(self, ordered: list):
        top_score = ordered[0][1]
        self.toppers = [candidate for (candidate, freq) in ordered if freq == top_score]
        self.runner_ups = [candidate for (candidate, freq) in ordered if freq == top_score - 1]
        # to make it probably faster later, provided that we are using Python 3.7+ or cpython 3.6
        self.votes = dict(ordered)

    def copy(self) -> 'Status':
        new = self.__class__.__new__(Status)
        if self.votes:
            new.votes = self.votes.copy()
        if self.toppers:
            new.toppers = self.toppers.copy()
        if self.runner_ups:
            new.runner_ups = self.runner_ups.copy()
        return new

    def __repr__(self):
        # return str([candidate.name[0] for (candidate, freq) in self.votes.items()])
        return str(list(self.in_order()))


class VoterTypes(Enum):
    general = auto()
    truthful = auto()
    lazy = auto()


class Voter:

    position: int = None
    profile: list = None
    utility: Utility = None
    most_recent_vote: Candidate = None

    def __init__(self, position: int, utility: Utility = BordaUtility):
        self.position = position
        self.utility = utility

    def __repr__(self):
        return f"{self.__class__.__name__}({self.position})\t{self.profile}"

    # def build_profile(self, candidates: list = None, profile: 'ProfilePreference' = SinglePeakedProfilePreference()):
    def build_profile(self, candidates: list = None, profile=None):
        self.profile = profile.build_profile(self, candidates)
        # Will need that later
        self.most_recent_vote = self.get_truthful_vote()

    @classmethod
    def make_voter(cls, voter_type: str, position: int, utility: Utility = BordaUtility) -> 'Voter':
        new = {
            VoterTypes.general.name: cls.__new__(GeneralVoter),
            VoterTypes.truthful.name: cls.__new__(TruthfulVoter),
            VoterTypes.lazy.name: cls.__new__(LazyVoter),
        }.get(voter_type, None)
        cls.__init__(new, position, utility)
        return new

    def get_truthful_vote(self) -> Candidate:
        return self.profile[0]

    def getprofile(self) -> list:
        return self.profile

    def propose_enhancement(self, current_status: Status, tie_breaking_rule: TieBreakingRule) -> UpdateEvent:
        """Evaluate the current status and return an update event

        - In case the voter is satistfied, frm and to will be the same.
        - In case the voter can make a difference, the update will be complete.
        - In case no improvement can be done, the update event will have only 'self', but frm and to are None.
            -- That can be overridden later in subclasses
                --- TruthfulVoter, can populate frm with self.most_recent_vote and to with self.get_truthful_vote()
                --- LazyVoter can populate to with NO_OPTION

        :param current_status: the actual current status object
        :param tie_breaking_rule: the tie breaking rule in effect (lexicographically or random)
        :return:
        """
        utility = self.utility
        frm = self.most_recent_vote
        winners = current_status.toppers
        runner_ups = current_status.runner_ups

        'The only case I am fully satisfied'
        if len(winners) == 1 and winners[0] == self.get_truthful_vote():
            return UpdateEvent(self, frm, frm)

        """OK He is not the winner, can I promote one of the top drawers (My choice may or may not be among them), to 
        be the sole winner?"""
        "Update: I am going to include the runner ups list in the same loop:"
        "Let's now try to upgrade one of the runner ups to compete with top list" """(as well)"""
        current_utility = utility.total_utility(self.profile, winners, tie_breaking_rule)
        proposed_status = current_status.copy()
        potential_updates = []
        # for candidate in toppers:
        combined_list = list(winners)
        combined_list.extend(runner_ups)
        for candidate in combined_list:

            if candidate == frm:
                continue

            proposed_status.votes[frm] = proposed_status.votes[frm] - 1
            proposed_status.votes[candidate] = proposed_status.votes[candidate] + 1
            proposed_status.in_order()

            potential_utility = utility.total_utility(self.profile, proposed_status.toppers, tie_breaking_rule)
            if potential_utility > current_utility:
                # potential_updates.append((potential_utility, candidate))
                potential_updates.append((potential_utility, candidate, current_utility))

            proposed_status.votes[frm] = proposed_status.votes[frm] + 1
            proposed_status.votes[candidate] = proposed_status.votes[candidate] - 1
        proposed_status.in_order()

        if len(potential_updates) == 0:
            'I can not improve'
            return UpdateEvent(self, frm, None)
        else:
            potential_updates.sort(key=operator.itemgetter(0), reverse=True)

            # potential_updates = [update for update in potential_updates if update[0] == potential_updates[0][0]]
            potential_updates = list(filter(lambda update: update[0] == potential_updates[0][0], potential_updates))
            # print(potential_updates)
            # enhance the selection process: select the nearest candidate to me among several alternatives
            "TODO was the previous line in the requirements?"
            if len(potential_updates) > 1:
                potential_updates.sort(key=lambda update: (update[1]).distance_to(self.position))

            to = potential_updates[0][1]
            self.most_recent_vote = to
            return UpdateEvent(self, frm, to)

    def vote(self, current_state: Status, tie_breaking_rule: TieBreakingRule = None) -> UpdateEvent:
        if self.profile is None:
            raise RuntimeError("Please create a profile first")
        return self.propose_enhancement(current_state, tie_breaking_rule)


class GeneralVoter(Voter):

    def vote(self, current_state: Status, tie_breaking_rule: TieBreakingRule = None) -> UpdateEvent:
        return super(GeneralVoter, self).vote(current_state, tie_breaking_rule)


class TruthfulVoter(Voter):

    def vote(self, current_state: Status, tie_breaking_rule: TieBreakingRule = None) -> UpdateEvent:
        update = super(TruthfulVoter, self).vote(current_state, tie_breaking_rule)
        if update.to is None:
            update.to = self.get_truthful_vote()
        return update


class LazyVoter(Voter):

    def __init__(self, position: int, utility: Utility = BordaUtility):
        super(LazyVoter, self).__init__(position, utility)
        self.abstain: bool = False
        self.abstain_event = UpdateEvent(self)

    def vote(self, current_state: Status, tie_breaking_rule: TieBreakingRule = None) -> UpdateEvent:
        if self.abstain:
            return self.abstain_event
        update = super(LazyVoter, self).vote(current_state, tie_breaking_rule)
        if update.to is None:
            self.abstain = True
            update.to = Candidate.NONE
            # update = self.abstain_event
        return update


######################################
if __name__ == '__main__':
    g = Voter.make_voter('GeneralVoter', 2)
    print(g)
    t = Voter.make_voter('TruthfulVoter', 2)
    print(t)
    lzy = Voter.make_voter('LazyVoter', 2)
    print(lzy)

    print(Voter.make_voter('TruthfulVoter', 4))
    print(Voter.make_voter('LazyVoter', 3))

    status = Status.from_profile([
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
        ])
    orderedCandidates = status.in_order()
    print(orderedCandidates)
    print(status.toppers)
    print(status.runner_ups)
