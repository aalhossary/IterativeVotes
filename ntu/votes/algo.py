import operator
import random

from ntu.votes.candidate import Candidate
import ntu.votes.voter as v


class TieBreakingRule:
    @staticmethod
    def get_winner(potential_winners: list) -> Candidate:
        """break a tie between potential winners

        :param potential_winners: the list (set ?) of potential winners with a tie
        :return: One of the potential winners according to some rule or random
        :raise ValueError If list has less than 2 candidates
        """
        raise NotImplementedError

    @staticmethod
    def winning_probability(potential_winners: list, candidate: Candidate):
        """Calculate the propability a candidate wins in tie breaking

        This function does not throw an exception. If a candidate is NOT in the list, it simply returns 0.
        :param potential_winners: list (set ?) of potential winners with tie
        :param candidate: the query candidate
        :return: the probability that this candidate will will
        """
        raise NotImplementedError

    @staticmethod
    def check_list_length(potential_winners):
        ln = len(potential_winners)
        if ln < 2:
            raise ValueError(f'There is no tie. List has only {ln} candidate(s)')


class LexicographicTieBreakingRule(TieBreakingRule):
    __doc__ = '''Fixed and predefined rule to prefer candidate A to B
    '''

    # sort_key = operator.attrgetter('name', 'position')

    @staticmethod
    def get_winner(potential_winners: list) -> Candidate:
        TieBreakingRule.check_list_length(potential_winners)
        sorted_list = sorted(potential_winners)#, key=LexicographicTieBreakingRule.sort_key)
        return sorted_list[0]

    @staticmethod
    def winning_probability(potential_winners: list, candidate: Candidate) -> int:
        if len(potential_winners) == 0:
            return 0
        try:
            return 1 if candidate == LexicographicTieBreakingRule.get_winner(potential_winners) else 0
        except (ValueError, RuntimeError):
            return 0


class RandomTieBreakingRule(TieBreakingRule):
    @staticmethod
    def get_winner(potential_winners: list) -> Candidate:
        TieBreakingRule.check_list_length(potential_winners)
        'TODO consider using chaoises later'
        'TODO ensure reproducibility'
        return random.choice(potential_winners)

    @staticmethod
    def winning_probability(potential_winners: list, candidate: Candidate):
        if candidate in potential_winners:
            return 1 / len(potential_winners)
        else:
            return 0


#################################################
class ProfilePreference:

    @staticmethod
    def build_profile(voter: v.Voter, candidates: list) -> list:
        raise NotImplementedError


class SinglePeakedProfilePreference(ProfilePreference):

    @staticmethod
    def build_profile(voter: v.Voter, candidates: list) -> list:
        distances = [(candidate.distance_to(voter.position), candidate) for candidate in candidates]
        # print(distances)
        '''TODO shall it be itemgetter(0,1) or itemgetter(0) only?
        i.e. after ordering based on the distance to voter, shall follow the original order or include lexicographical 
        ordering of the candidates as well? '''
        distances.sort(key=operator.itemgetter(0, 1))
        # print(distances)
        return [c for d, c in distances]


class GeneralProfilePreference(ProfilePreference):
    @staticmethod
    def build_profile(voter: v.Voter, candidates: list) -> list:
        """"TODO ensure reproducibility"""
        temp = candidates.copy()
        random.shuffle(temp)
        return temp


#################################################

class UpdateEvent:
    def __init__(self, source: v.Voter = None, frm: Candidate = None, to: Candidate = None):
        self.source = source
        self.frm = frm
        self.to = to

    def __repr__(self):
        return str((self.source, self.frm, self.to))


class Status:
    __votes__ = {}

    def fillstatus(self, profile):
        votes = {}







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

    rule = LexicographicTieBreakingRule
    winner = rule.get_winner(cc)
    print(winner)
    print(rule.winning_probability(cc, cc[0]))
    print(rule.winning_probability(cc, winner))
    print(rule.winning_probability(cc, Candidate('A', 5)))

    # ----------------------
    rule = RandomTieBreakingRule
    winner = rule.get_winner(cc)
    print(winner)
    print(rule.winning_probability(cc, cc[0]))
    print(rule.winning_probability(cc, winner))
    print(rule.winning_probability(cc, Candidate('A', 5)))

    # ------------------------
    preference: ProfilePreference = None
    preference = SinglePeakedProfilePreference
    print(preference.build_profile(v.Voter(2), cc))

    preference = GeneralProfilePreference
    print(preference.build_profile(v.Voter(2), cc))
    print(preference.build_profile(v.Voter(2), cc))

