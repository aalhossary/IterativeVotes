import itertools

import math
from random import Random
import matplotlib.pyplot as plt
import sys
import os
from mpi4py import MPI

from docopt import docopt
from ntu.votes.candidate import *
from ntu.votes.profilepreference import *
from ntu.votes.tiebreaking import *
from ntu.votes.utility import *
from ntu.votes.voter import *


class Measurements:
    """Holds the complete set of measures of (50?) alleles: same voters, same candidates, same profile, different
    random scenarios."""
    n_voters: int
    n_candidates: int
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
        return f"n_voters = {self.n_voters}\n" \
            f"n_candidates = {self.n_candidates}\n" \
            f"percentage_of_convergence = {self.percentage_of_convergence}\n" \
            f"averageTimeToConvergence = {self.averageTimeToConvergence}\n" \
            f"averageSocial_welfare = {self.averageSocial_welfare}\n" \
            f"stable_states_sets: count = {len(self.stable_states_sets)}, repr = {[set(s) for s in self.stable_states_sets]}\n" \
            f"winning_sets: count = {len(self.winning_sets)}, repr = {[set(s) for s in self.winning_sets]}\n" \
            f"percentage_truthful_winner_wins = {self.percentage_truthful_winner_wins}%\n" \
            f"percentage_winner_is_weak_condorcet = {self.percentage_winner_is_weak_condorcet}%\n" \
            f"percentage_winner_is_strong_condorcet = {self.percentage_winner_is_strong_condorcet}%\n"


def aggregate_alleles(alleles: list, all_voters: list, profile: list, utility: Utility, tiebreakingrule: TieBreakingRule) -> Measurements:
    measurements = Measurements()
    measurements.n_voters = len(profile)  # len(all_voters) is also OK
    measurements.n_candidates = len(profile[0])
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
        result[query] = 0
        result[other] = 0
        for voter_profile in profile:
            for candidate in voter_profile:
                # They are ordered according to preference. Who appears first is the voter's winner
                if candidate == query:
                    result[query] = result[query] + 1
                    break
                elif candidate == other:
                    result[other] = result[other] + 1
                    break
        if result[query] < result[other]:
            return False
        elif strong_only and result[query] == result[other]:
            return False
    return True


def main():
    doc = """Iterative voting engine

Usage:
  Engine.py [options]
  Engine.py [options] [--utility borda]
  Engine.py [options] [--utility expo [<BASE> [<EXPO_STEP>]]]


Options:
  -c, --cmin=CMIN   Min number of candidates    [Default: 5]
  -C, --cmax=CMAX   Max number of candidates    [Default: 7]
  -v, --vmin=VMIN   Min number of Voters        [Default: cmin]
  -V, --vmax=VMAX   Max number of Voters        [Default: 12]
  -l, --log=LFILE   Log file (if ommitted or -, output to stdout)   [Default: -]
  -o, --out-folder=OFOLDER      Output folder where all scenarios are written [Default: ./out]
  -u, --utility=UTILITY         User Utility function (borda | expo)[Default: borda]
  -p, --preference=PREFERENCE   How a voter forms his ballot 
                                order (single-peaked | general)     [Default: single-peaked]
  -t, --tiebreakingrule=TIEBREAKINGRULE     How to behave in cases of draws 
                                (lexicographic | random)            [Default: lexicographic]
  --voters=VOTERS       Type of voters (general | truthful | lazy)  [Default: general]
  -s, --seed=SEED       Randomization seed     [Default: 12345]
  -h, --help            Print the help screen
  --version             Prints the version and exits
  BASE                  The base               [default: 2]
  EXPO_STEP             The exponent increment [Default: 1]


"""

    comm = MPI.COMM_WORLD
    args = docopt(doc, version='0.1.0')
    # print(args)
    seed = int(args['--seed'])
    all_simulations_per_all_seeds = dict()
    log = out = None

    seeds_rank = comm.Get_rank()
    seeds_num_processors = comm.Get_size()
    seeds_all_previously_run_count = 0
    seeds_run_base = seed
    seeds_run_size = 100  # initially 100, later will be half sum seeds_all_previously_run_count + last seeds_run_size
    seeds_chunk_size = int(math.ceil(seeds_run_size / seeds_num_processors))
    seeds_chunk_base = seeds_run_base + (seeds_rank * seeds_chunk_size)
    # print(seeds_run_size, seeds_rank, seeds_run_base, seeds_run_size, seeds_chunk_size, seeds_chunk_base)

    for assigned_seed in range(seeds_chunk_base,
                               min((seeds_chunk_base + seeds_chunk_size), (seeds_run_base + seeds_run_size))):
        log_arg = args['--log']
        if log_arg == '-':
            log = sys.stdout
        else:
            if not os.path.exists(log_arg):
                dirname = os.path.dirname(log_arg)
                if dirname != '':  # If just a file name without a folder
                    os.makedirs(dirname, exist_ok=True)
            log = open(log_arg, 'w')

        out_path = os.path.join(args['--out-folder'], f'out-{assigned_seed}.log')
        if not os.path.exists(out_path):
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
        out = open(out_path, 'w')

        # to be run in a separate MPI process or node
        args["assigned_seed"] = assigned_seed
        args['log'] = log
        args['out'] = out
        all_simulations_per_all_seeds[assigned_seed] = run_all_simulations_per_seed(args)
        out.close()
    # collect the simulations results from several threads
    buffer = comm.gather(all_simulations_per_all_seeds, root=0)
    if seeds_rank == 0:
        for dct in buffer:
            for item in dct.items():
                print(item[0])
                for msrmnt in item[1]:
                    print(str(msrmnt))

    log.write("Done.\n")
    log.close()

    # # print(average_time_to_convergence)
    # # print(list(zip(*average_time_to_convergence)))
    # plot_it(average_time_to_convergence, 'average time to convergence', n_candidates_range, n_voters_range)
    # plot_it(average_social_welfare, 'average social welfare', n_candidates_range, n_voters_range)
    # plot_it(percentage_of_convergence, 'percentage of convergence', n_candidates_range, n_voters_range)
    # plot_it(num_stable_states_sets, 'num stable states', n_candidates_range, n_voters_range)


def run_all_simulations_per_seed(args) -> list:
    """Run different candidates numbers [5-7]* different voters numbers [cmin -12]* 50 repeat

    :param args: all arguments after adjusting THIS suit seed
    :return: list of measures, one for every profile (candidates/voters/preferences)
    """
    out = args['out']
    log = args['log']
    utility = {
        'borda': BordaUtility(),
        'expo': ExpoUtility(base=args.get('<BASE>', 2),
                            exponent_step=args.get('<EXPO_STEP>', 1)),
    }.get(args['--utility'], None)
    cmin = int(args['--cmin'])
    cmax = int(args['--cmax'])
    # vmin = int(args['--vmin'])
    vmin = cmin if 'cmin' == args['--vmin'] else int(args['--vmin'])
    vmax = int(args['--vmax'])
    rand = random.Random(args['assigned_seed'])
    preference = {
        'single-peaked': SinglePeakedProfilePreference(),
        'general': GeneralProfilePreference(rand),
    }.get(args['--preference'], None)
    tie_breaking_rule = {
        'lexicographic': LexicographicTieBreakingRule(),
        'random': RandomTieBreakingRule(rand),
    }.get(args['--tiebreakingrule'], None)
    # print(utility, preference, tie_breaking_rule)
    all_profiles_measurements = []
    n_candidates_range = range(cmin, cmax + 1)
    for n_candidates in n_candidates_range:
        # number of n_candidates <= n_voters <= 12
        n_voters_range = range(max(vmin, n_candidates), vmax + 1)
        for n_voters in n_voters_range:
            if n_voters % 2:
                continue

            out.write(f'\n------------ voters = {n_voters}, Candidates = {n_candidates}-------------------\n')
            log.write(f'\n------------ voters = {n_voters}, Candidates = {n_candidates}-------------------\n')
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
                streams = {'log': log, 'out': out}
                scenario = run_simulation(all_candidates, all_voters, initial_status, tie_breaking_rule, rand, **streams)
                alleles.append(scenario)
            measurements = aggregate_alleles(alleles, all_voters, profile, utility, tie_breaking_rule)
            log.write("-------measurements\n")
            log.write(str(measurements)+'\n')
            log.write("-------\n")

            all_profiles_measurements.append(measurements)
            # average_time_to_convergence.append(measurements.averageTimeToConvergence)
            # average_social_welfare.append(measurements.averageSocial_welfare)
            # percentage_of_convergence.append(measurements.percentage_of_convergence)
            # num_stable_states_sets.append(len(measurements.stable_states_sets))
    return all_profiles_measurements


def run_simulation(all_candidates: list, all_voters: list, current_status: Status, tie_breaking_rule: TieBreakingRule,
                   rand: Random, **streams) -> list:
    """

    :param tie_breaking_rule:
    :param current_status:
    :param all_voters:
    :param all_candidates:
    :param rand:
    :type rand: Random
    """
    # log = streams['log']
    out = streams['out']
    scenario = []
    # only increase
    abstaining_voters_indices = []
    # now for the initial status
    out.write(f'{current_status}\tInitial state\n')
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

            out.write(f'{current_status}\t{index:#2}\t{response}\t')
            # evaluate the status
            if response.to is None:
                # couldn't enhance
                active_voters_indices.remove(index)
                if isinstance(voter, LazyVoter):
                    abstaining_voters_indices.append(index)

                if len(active_voters_indices):
                    out.write('\n')
                else:
                    return converged(current_status, scenario, **streams)
            # elif response.frm == response.to:
            #     # voter was satisfied (currently a dead case)
            #     out.write('\n')
            else:
                out.write("<-- enhancement\n")
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
            return not_converged(current_status, scenario, **streams)
    else:
        return not_converged(current_status, scenario, **streams)


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


def converged(last_status: Status, scenario: list, **streams) -> list:
    out = streams['out']
    out.write("Converged\n")
    out.write(f'{last_status}\tFinal state\n')
    scenario.append(last_status.copy())
    scenario.append(True)
    return scenario


def not_converged(last_status: Status, scenario: list, **streams) -> list:
    out = streams['out']
    out.write(last_status, "No convergence\n")
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
