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
    votes: dict = None
    winners: list = None
    runner_ups: list = None

    @classmethod
    def from_profile(cls, profile: list) -> 'Status':
        votes = [user_profile[0] for user_profile in profile]
        return cls.from_votes(votes)

    @classmethod
    def from_votes(cls, votes: list) -> 'Status':
        new = cls.__new__(Status)
        new.votes = {}
        for candidate in votes:
            new.votes[candidate] = new.votes.get(candidate, 0) + 1
        ordered = new.in_order()
        return new

    def in_order(self) -> list:
        """Return the votes as a list of frequencies, and cache the top two groups (winners and runner ups)."""
        lst = list(self.votes.items())
        """If using Python 3.7, dictionary order is guaranteed to be preserved"""
        lst.sort(key=operator.itemgetter(1), reverse=True)
        self.cache_top_candidates(lst)
        return lst

    def cache_top_candidates(self, ordered: list):
        top_score = ordered[0][1]
        self.winners = [candidate for (candidate, freq) in ordered if freq == top_score]
        self.runner_ups = [candidate for (candidate, freq) in ordered if freq == top_score - 1]
        # to make it probably faster later, provided that we are using Python 3.7+ or cpython 3.6
        self.votes = dict(ordered)

    def copy(self) -> 'Status':
        new = self.__class__.__new__(Status)
        if self.votes:
            new.votes = self.votes.copy()
        if self.winners:
            new.winners = self.winners.copy()
        if self.runner_ups:
            new.runner_ups = self.runner_ups.copy()
        return  new


class VoterTypes(Enum):
    GeneralVoter = auto()
    TruthfulVoter = auto()
    LazyVoter = auto()


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
    def make_voter(cls, voter_type: VoterTypes, position: int, utility: Utility = BordaUtility) -> 'Voter':
        new = {
            VoterTypes.GeneralVoter: cls.__new__(GeneralVoter),
            VoterTypes.TruthfulVoter: cls.__new__(TruthfulVoter),
            VoterTypes.LazyVoter: cls.__new__(LazyVoter),
        }.get(voter_type, None)
        cls.__init__(new, position, utility)
        return new

    def get_truthful_vote(self) -> Candidate:
        return self.profile[0]

    def getprofile(self) -> list:
        return self.profile

    def propose_enhancement(self, current_status: Status, tiebreakingrule: TieBreakingRule) -> UpdateEvent:
        """Evaluate the current status and return an update event

        - In case the voter is satistfied, frm and to will be the same.
        - In case the voter can make a difference, the update will be complete.
        - In case no improvement can be done, the update event will have only 'self', but frm and to are None.
            -- That can be overridden later in subclasses
                --- TruthfulVoter, can populate frm with self.most_recent_vote and to with self.get_truthful_vote()
                --- LazyVoter can populate to with NO_OPTION

        :param current_status: the actual current status object
        :param tiebreakingrule: the tie breaking rule in effect (lexicographically or random)
        :return:
        """
        utility = self.utility
        frm = self.most_recent_vote
        winners = current_status.winners
        runner_ups = current_status.runner_ups

        'The only case I am fully satisfied'
        if len(winners) == 1 and winners[0] == self.get_truthful_vote():
            return UpdateEvent(self,frm,frm)

        """OK He is not the winner, can I promote one of the top drawers (My choice may or may not be among them), to 
        be the sole winner?"""
        "Update: I am going to include the runner ups list in the same loop:"
        "Let's now try to upgrade one of the runner ups to compete with top list" """(as well)"""
        current_utility = utility.total_utility(self.profile, winners, tiebreakingrule)
        proposed_status = current_status.copy()
        potential_updates = []
        # for candidate in winners:
        combined_list = list(winners)
        combined_list.extend(runner_ups)
        for candidate in combined_list:

            if candidate == frm:
                continue

            proposed_status.votes[frm] = proposed_status.votes[frm] - 1
            proposed_status.votes[candidate] = proposed_status.votes[candidate] + 1
            proposed_status.in_order()

            potential_utility = utility.total_utility(self.profile, proposed_status.winners, tiebreakingrule)
            if potential_utility > current_utility:
                potential_updates.append((potential_utility, candidate))

            proposed_status.votes[frm] = proposed_status.votes[frm] + 1
            proposed_status.votes[candidate] = proposed_status.votes[candidate] - 1
        proposed_status.in_order()

        if len(potential_updates) == 0 :
            'I can not improve'
            return UpdateEvent(self, frm, None)
        else:
            "TODO enhance the selection process: select the nearest candidate to me among several alternatives"
            "TODO was the previous line in the requirements?"
            potential_updates.sort(key=operator.itemgetter(0, 1), reverse=True)

            # Is there a (map / filter) way to do the next line?
            potential_updates = [update for update in potential_updates if update[0] == potential_updates[0][0]]
            if len(potential_updates) > 1:
                potential_updates.sort(key=lambda update: (update[0]).distance_to(self.position))

            to = potential_updates[0][1]
            return UpdateEvent(self, frm, to)

    def vote(self, current_state: Status, tiebreakingrule: TieBreakingRule=None) -> UpdateEvent:
        if self.profile is None:
            raise RuntimeError("Please create a profile first")
        return self.propose_enhancement(current_state, tiebreakingrule)


class GeneralVoter(Voter):

    def vote(self, current_state: Status, tiebreakingrule: TieBreakingRule=None) -> UpdateEvent:
        super().vote(current_state)
        return self.propose_enhancement(current_state, tiebreakingrule)


class TruthfulVoter(Voter):

    def vote(self, current_state: Status, tiebreakingrule: TieBreakingRule=None) -> UpdateEvent:
        super().vote(current_state)
        update = self.propose_enhancement(current_state, tiebreakingrule)
        if update.to is None:
            update.to = self.get_truthful_vote()
        return update


class LazyVoter(Voter):

    def __init__(self, position: int, utility: Utility = BordaUtility):
        super(LazyVoter, self).__init__(self, position, utility)
        self.abstain: bool = False
        self.abstain_event = UpdateEvent(self)

    def vote(self, current_state: Status, tiebreakingrule: TieBreakingRule=None) -> UpdateEvent:
        if self.abstain:
            return self.abstain_event

        super().vote(current_state)
        update = self.propose_enhancement(current_state, tiebreakingrule)
        if update.to is None:
            self.abstain = True
            # TODO revise what should be returned (self, None, Candidate.NONE)
            #  or (self, most_recent_vote, Candidate.NONE).
            # update.to = Candidate.NONE
            update = self.abstain_event
        return update


######################################
if __name__ == '__main__':
    g = Voter.make_voter(VoterTypes.GeneralVoter, 2)
    print(g)
    t = Voter.make_voter(VoterTypes.TruthfulVoter, 2)
    print(t)
    lzy = Voter.make_voter(VoterTypes.LazyVoter, 2)
    print(lzy)

    print(Voter.make_voter(VoterTypes.TruthfulVoter, 4))
    print(Voter.make_voter(VoterTypes.LazyVoter, 3))

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
    print(status.winners)
    print(status.runner_ups)


