import argparse
import itertools
from random import Random
import matplotlib.pyplot as plt
import sys

from docopt import docopt
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


class Measurements:
    """Holds the complete set of measures of (50?) runs of a single profile."""
    percentage_of_convergence: float
    averageTimeToConvergence: float
    averageSocial_welfare: float
    # How many different stable states we have across all iteration sequences of the same preference profile
    stable_states_sets: set
    winning_sets: set
    percentage_truthful_winner_wins: float
    percentage_winner_is_weak_condorcet: float
    percentage_winner_is_strong_condorcet: float

    def __init__(self):
        self.stable_states_sets = set()
        self.winning_sets = set()

    def __str__(self):
        return f"percentage_of_convergence = {self.percentage_of_convergence}\n" \
            f"averageTimeToConvergence = {self.averageTimeToConvergence}\n" \
            f"averageSocial_welfare = {self.averageSocial_welfare}\n" \
            f"stable_states_sets: count = {len(self.stable_states_sets)}, repr = {self.stable_states_sets}\n" \
            f"winning_sets: count = {len(self.winning_sets)}, repr = {self.winning_sets}\n" \
            f"percentage_truthful_winner_wins = {self.percentage_truthful_winner_wins}%\n" \
            f"percentage_winner_is_weak_condorcet = {self.percentage_winner_is_weak_condorcet}%\n" \
            f"percentage_winner_is_strong_condorcet = {self.percentage_winner_is_strong_condorcet}%\n"


def aggregate_alleles(alleles, all_voters, profile, utility: Utility, tiebreakingrule: TieBreakingRule) -> Measurements:
    measurements = Measurements()
    convergence_counter = welfare = truthful_winner_wins_counter = winner_is_weak_condorcet_counter = \
        winner_is_strong_condorcet_counter = 0.0
    steps_before_convergence = []
    for allele in alleles:
        initial_state: Status = allele[0]
        converged: bool = allele[-1]
        final_status = allele[-2]
        # lastAction: UpdateEvent = allele[-3] # not needed
        final_status_toppers = final_status.toppers

        if isinstance(tiebreakingrule, RandomTieBreakingRule):
            initial_winner_s = frozenset(initial_state.toppers)
            final_winner_s = frozenset(final_status_toppers)
        elif isinstance(tiebreakingrule, LexicographicTieBreakingRule):
            initial_winner_s = frozenset([tiebreakingrule.get_winner(initial_state.toppers)])
            final_winner_s = frozenset([tiebreakingrule.get_winner(final_status_toppers)])
        else:
            raise TypeError("Tie breaking rule not known")

        measurements.winning_sets.add(final_winner_s)

        if initial_winner_s == final_winner_s:
            truthful_winner_wins_counter += 1

        if converged:
            convergence_counter += 1
            # initial state, final boolean, 2 entries each step
            steps_before_convergence.append((len(allele) - 1 - 1) / 2)
            # A stable states is simply the state of a converged system.
            measurements.stable_states_sets.add(final_winner_s)

        for voter in all_voters:
            welfare += utility.total_utility(voter.profile, final_status_toppers, tiebreakingrule)

        # if not is_condorset_winner(profile, final_status.toppers[0]):
        #     others = profile[0].copy()
        #     others.remove(final_status.toppers[0])
        #     for other in others:
        #         if is_condorset_winner(profile, other):
        #             print("found", other, repr(profile))

        for winner in final_winner_s:
            if not is_condorset_winner(profile, winner, week=True):
                break
        else:  # else of the (for loop), not of the (if statement)
            winner_is_weak_condorcet_counter += 1
            # test again for strong condorcet winner
            for winner in final_winner_s:
                if not is_condorset_winner(profile, winner, week=False):
                    break
            else:
                winner_is_strong_condorcet_counter += 1

    measurements.percentage_of_convergence = convergence_counter * 100.0 / len(steps_before_convergence)
    measurements.averageTimeToConvergence = sum(steps_before_convergence) / len(steps_before_convergence)
    measurements.averageSocial_welfare = welfare / len(alleles)
    measurements.percentage_truthful_winner_wins = truthful_winner_wins_counter * 100 / len(alleles)
    measurements.percentage_winner_is_weak_condorcet = winner_is_weak_condorcet_counter * 100 / len(alleles)
    measurements.percentage_winner_is_strong_condorcet = winner_is_strong_condorcet_counter * 100 / len(alleles)

    return measurements


def is_condorset_winner(profile: list, query: Candidate, week=True) -> bool:
    result = dict()
    strong_only = not week
    others = profile[0].copy()
    others.remove(query)
    for other in others:
        result.clear()
        for voter_profile in profile:
            for candidate in voter_profile:
                # They are ordered according to preference. Who appears first is the voter's winner
                if candidate is query:
                    result[query] = result.get(query, 0) + 1
                    break
                elif candidate is other:
                    result[other] = result.get(other, 0) + 1
                    break
        if result[query] < result[other]:
            return False
        elif strong_only and result[query] == result[other]:
            return False
    return True


def main():
    __doc__ = '''Iterative voting engine

Usage:
  Engine.py [options]
  Engine.py [options] [--utility borda]
  Engine.py [options] [--utility expo [<BASE> [<EXPO_STEP>]]]


Options:
  -c, --cmin=CMIN   Min number of candidates    [Default: 5]
  -C, --cmax=CMAX   Max number of candidates    [Default: 7]
  -v, --vmin=VMIN   Min number of Voters        [Default: cmin]
  -V, --vmax=VMAX   Max number of Voters        [Default: 12]
  -u, --utility=UTILITY         User Utility function (borda | expo) [Default: borda]
  -p, --preference=PREFERENCE   How a voter forms his ballot 
                                order (single-peaked | general) [Default: single-peaked]
  -t, --tiebreakingrule=TIEBREAKINGRULE     How to behave in cases of draws 
                                (lexicographic | random) [Default: lexicographic]
  --voters=VOTERS       Type of voters (general | truthful | lazy) [Default: general]
  -s, --seed=SEED       Randomization seed     [Default: 12345]
  -h, --help            Print the help screen
  --version             Prints the version and exits
  BASE                  The base               [default: 2]
  EXPO_STEP             The exponent increment [Default: 1]


'''

    args = docopt(__doc__, version='0.1.0')
    print(args)

    rand = random.Random(args['--seed'])

    # if args.candidates:
    #     print("candidates = ", args.candidates)
    # if args.voters:
    #     print("voters = ", args.voters)

    utility = {
        'borda': BordaUtility(),
        'expo': ExpoUtility(base=args.get('<BASE>', 2),
                            exponent_step=args.get('<EXPO_STEP>', 1)),
    }.get(args['--utility'], None)

    preference = {
        'single-peaked': SinglePeakedProfilePreference(),
        'general': GeneralProfilePreference(rand),
    }.get(args['--preference'], None)

    tie_breaking_rule = {
        'lexicographic': LexicographicTieBreakingRule(),
        'random': RandomTieBreakingRule(rand),
    }.get(args['--tiebreakingrule'], None)

    print(utility, preference, tie_breaking_rule)
    percentage_of_convergence = []
    average_time_to_convergence = []
    average_social_welfare = []
    num_stable_states_sets = []

    cmin = int(args['--cmin'])
    cmax = int(args['--cmax'])
    vmin = int(args['--cmin'])
    vmin = cmin if vmin == 'cmin' else int(vmin)
    vmax = int(args['--vmax'])

    n_candidates_range = range(cmin, cmax + 1)
    n_voters_range = []
    for n_candidates in n_candidates_range:
        # number of n_candidates <= n_voters <= 12
        n_voters_range = range(max(vmin, n_candidates), vmax + 1)
        for n_voters in n_voters_range:
            if n_voters % 2:
                continue

            print(f"\n------------ voters = {n_voters}, Candidates = {n_candidates}-------------------")
            all_candidates = generate_candidates(n_candidates, rand)
            # print(all_candidates)
            all_voters = generate_voters(n_voters, args['--voters'], utility, rand)
            # print(all_voters)

            # voters build their preferences
            for voter in all_voters:
                voter.build_profile(all_candidates, preference)
            # collective profile
            profile = [voter.getprofile() for voter in all_voters]
            initial_status = Status.from_profile(profile)

            alleles = []
            for run in range(50):
                scenario = run_simulation(all_candidates, all_voters, initial_status, tie_breaking_rule, rand)
                alleles.append(scenario)
            measurements = aggregate_alleles(alleles, all_voters, profile, utility, tie_breaking_rule)
            print("-------measurements")
            print(measurements)
            print("-------")

            average_time_to_convergence.append((n_candidates, n_voters, measurements.averageTimeToConvergence))
            average_social_welfare.append((n_candidates, n_voters, measurements.averageSocial_welfare))
            percentage_of_convergence.append((n_candidates, n_voters, measurements.percentage_of_convergence))
            num_stable_states_sets.append((n_candidates, n_voters, len(measurements.stable_states_sets)))

    # print(average_time_to_convergence)
    # print(list(zip(*average_time_to_convergence)))
    plot_it(average_time_to_convergence, 'average time to convergence', n_candidates_range, n_voters_range)
    plot_it(average_social_welfare, 'average social welfare', n_candidates_range, n_voters_range)
    plot_it(percentage_of_convergence, 'average time to convergence', n_candidates_range, n_voters_range)
    plot_it(num_stable_states_sets, 'num stable states', n_candidates_range, n_voters_range)


def run_simulation(all_candidates: list, all_voters: list, current_status: Status, tie_breaking_rule: TieBreakingRule,
                   rand: Random) -> list:
    """

    :param tie_breaking_rule:
    :param current_status:
    :param all_voters:
    :param all_candidates:
    :param rand:
    :type rand: Random
    """
    scenario = []
    # only increase
    abstaining_voters_indices = []
    # now for the initial status
    print(current_status, "Initial state")
    scenario.append(current_status.copy())
    step = 0
    max_steps = len(all_voters) * len(all_candidates)
    while step < max_steps:
        # recalculated every step, always decrease
        active_voters_indices = list(itertools.filterfalse(lambda i: i in abstaining_voters_indices,
                                                           range(len(all_voters))))
        n_toppers = len(current_status.toppers)
        if n_toppers < 2:
            active_voters_indices = list(
                itertools.filterfalse(lambda i: all_voters[i].most_recent_vote is current_status.toppers[0],
                                      active_voters_indices))
        else:
            # This condition needs to be double checked for all corner cases
            active_voters_indices = list(
                filter(lambda i: tie_breaking_rule.winning_probability(
                    current_status.toppers, all_voters[i].most_recent_vote) < (1 / n_toppers),
                       active_voters_indices))

        status_changed = bool
        # Select one voter randomly from Current active_voters_indices list
        while len(active_voters_indices) > 0 and step < max_steps:  # Note that we check number of steps as well
            status_changed = False
            # pick a voter from ACTIVE voters
            index = rand.choice(active_voters_indices)
            voter = all_voters[index]
            # ask him to vote
            response = voter.vote(current_status, tie_breaking_rule)
            scenario.append(response)
            step += 1

            print(current_status, f'{index:#2}', response, end='\t')
            # evaluate the status
            if response.to is None:
                # couldn't enhance
                active_voters_indices.remove(index)
                if isinstance(voter, LazyVoter):
                    abstaining_voters_indices.append(index)

                if len(active_voters_indices):
                    print()
                else:
                    return converged(current_status, scenario)
            # elif response.frm is response.to:
            #     # voter was satisfied (currently a dead case)
            #     print()
            else:
                print("<-- enhancement")
                current_status.votes[response.frm] = current_status.votes[response.frm] - 1
                current_status.votes[response.to] = current_status.votes[response.to] + 1
                current_status.in_order()

                scenario.append(current_status.copy())
                status_changed = True
                break

        if status_changed:
            # last step was successful
            continue
        else:
            # max steps exhausted
            return not_converged(current_status, scenario)
    else:
        return not_converged(current_status, scenario)


def plot_it(passed_in_array, label: str, n_candidates_range, n_voters_range):
    for n_candidates in n_candidates_range:
        new_list = [(v, y) for (c, v, y) in passed_in_array if c == n_candidates]
        print("for candidates = ", n_candidates)
        print(new_list)
        separate_x_y = list(zip(*new_list))
        print("separate: ", separate_x_y)
        if separate_x_y:
            plt.plot(separate_x_y[0], separate_x_y[1], 'o-', label=f'candidates = {n_candidates}')
    plt.title(label)
    plt.legend()
    plt.xlabel('Voters')
    plt.show()

    for n_voters in n_voters_range:
        new_list = [(c, y) for (c, v, y) in passed_in_array if v == n_voters]
        print("for voters = ", n_voters)
        print(new_list)
        separate_x_y = list(zip(*new_list))
        print("separate: ", separate_x_y)
        if separate_x_y:
            plt.plot(separate_x_y[0], separate_x_y[1], '^-', label=f'voters = {n_voters}')
    plt.title(label)
    plt.legend()
    plt.xlabel('Candidates')
    plt.show()


def converged(last_status: Status, scenario: list) -> list:
    print("Converged")
    print(last_status, "Final state")
    scenario.append(last_status.copy())
    scenario.append(True)
    return scenario


def not_converged(last_status: Status, scenario: list) -> list:
    print(last_status, "No convergence")
    scenario.append(last_status.copy())
    scenario.append(False)
    return scenario


def generate_voters(n_voters: int, voter_type: str, utility: Utility, rand: Random):
    all_voters = []
    for i in range(n_voters):
        # v: Voter = Voter.make_voter(voter_type, rand.randrange(positions_range), utility)
        v: Voter = Voter.make_voter(voter_type, rand.random(), utility)
        all_voters.append(v)
    return all_voters


def generate_candidates(n_candidates: int, rand: Random):
    all_candidates = []
    for i in range(n_candidates):
        # c: Candidate = Candidate(chr(b'A'[0]+i), i+1)
        c: Candidate = Candidate(chr(b'A'[0]+i), rand.random())
        all_candidates.append(c)
    return all_candidates


# --------------------------
if __name__ == '__main__':
    main()
