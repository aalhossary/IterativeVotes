import itertools
import math
from random import Random
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from mpi4py import MPI

from docopt import docopt
from ntu.votes.candidate import *
from ntu.votes.profilepreference import *
from ntu.votes.tiebreaking import *
from ntu.votes.utility import *
from ntu.votes.voter import *
from helper import *


class Measurements:
    """Holds the complete set of measures of (50?) alleles: same voters, same candidates, same profile, different
    random scenarios."""
    n_voters: int
    n_candidates: int
    percentage_of_convergence: float
    average_time_to_convergence: float
    average_social_welfare: float
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
        sss = self.stable_states_sets
        ws = self.winning_sets
        return f"n_voters = {self.n_voters}\n" \
            f"n_candidates = {self.n_candidates}\n" \
            f"percentage_of_convergence = {self.percentage_of_convergence}\n" \
            f"average_time_to_convergence = {self.average_time_to_convergence}\n" \
            f"average_social_welfare = {self.average_social_welfare}\n" \
            f"stable_states_sets: count = {len(sss)}, repr = {[set(s) for s in sss]}\n" \
            f"winning_sets: count = {len(ws)}, repr = {[set(s) for s in ws]}\n" \
            f"percentage_truthful_winner_wins = {self.percentage_truthful_winner_wins}%\n" \
            f"percentage_winner_is_weak_condorcet = {self.percentage_winner_is_weak_condorcet}%\n" \
            f"percentage_winner_is_strong_condorcet = {self.percentage_winner_is_strong_condorcet}%"


def aggregate_alleles(alleles: list, all_voters: list, profile: list, utility: Utility,
                      tiebreakingrule: TieBreakingRule) -> Measurements:
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

        # if not is_condorcet _winner(profile, final_status.toppers[0]):
        #     others = profile[0].copy()
        #     others.remove(final_status.toppers[0])
        #     for other in others:
        #         if is_condorcet_winner(profile, other):
        #             print("found", other, repr(profile))

        for winner in final_winner_s:
            if not is_condorcet_winner(profile, winner, week=True):
                break
        else:  # else of the (for loop), not of the (if statement)
            winner_is_weak_condorcet_counter += 1
            # test again for strong condorcet winner
            for winner in final_winner_s:
                if not is_condorcet_winner(profile, winner, week=False):
                    break
            else:
                winner_is_strong_condorcet_counter += 1

    len_steps_before_convergence = len(steps_before_convergence)
    len_alleles = len(alleles)
    measurements.percentage_of_convergence = convergence_counter * 100.0 / len_steps_before_convergence \
        if len_steps_before_convergence else 100
    measurements.average_time_to_convergence = sum(steps_before_convergence) / len_steps_before_convergence \
        if len_steps_before_convergence else 0
    measurements.average_social_welfare = welfare / len_alleles  # TODO Discuss
    measurements.percentage_truthful_winner_wins = truthful_winner_wins_counter * 100 / len_alleles
    measurements.percentage_winner_is_weak_condorcet = winner_is_weak_condorcet_counter * 100 / len_alleles
    measurements.percentage_winner_is_strong_condorcet = winner_is_strong_condorcet_counter * 100 / len_alleles

    return measurements


def is_condorcet_winner(profile: list, query: Candidate, week=True) -> bool:
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
  engine.py [options]
  engine.py [options] [--utility borda]
  engine.py [options] [--utility expo [<BASE> [<EXPO_STEP>]]]


Options:
  -c, --cmin=CMIN   Min number of candidates    [Default: 5]
  -C, --cmax=CMAX   Max number of candidates    [Default: 7]
  -v, --vmin=VMIN   Min number of Voters        [Default: cmin]
  -V, --vmax=VMAX   Max number of Voters        [Default: 12]
  -l, --log=LFILE   Log file (if ommitted or -, output to stdout)               [Default: -]
  -o, --out-folder=OFOLDER      Output folder where all scenarios are written   [Default: ./out]
  -r, --random-search           Don't perform exhaustive search of profiles     [Default: Yes]
  -u, --utility=UTILITY         User Utility function (borda | expo)            [Default: borda]
  -p, --preference=PREFERENCE   How a voter forms his ballot order 
                                (single-peaked | general)                       [Default: single-peaked]
  --conv-threshold=THRESHOLD    Threshold of similarity of different profiles 
                                sampling before considering the curve converged [Default: 0.08]
  -t, --tiebreakingrule=TIEBREAKINGRULE     How to behave in cases of draws 
                                (lexicographic | random)                        [Default: lexicographic]
  -i, --initial-run-size=SIZE   Initial number of runs before testing for 
                                convergence                                     [Default: 100]
  --voters=VOTERS       Type of voters (general | truthful | lazy)              [Default: general]
  -s, --seed=SEED       Randomization seed      [Default: 12345]
  -h, --help            Print the help screen
  --version             Prints the version and exits
  BASE                  The base                [default: 2]
  EXPO_STEP             The exponent increment  [Default: 1]


"""

    args = docopt(doc, version='0.1.0')
    # print(args)
    seed = int(args['--seed'])
    all_simulations_per_all_seeds = dict()
    log = None

    comm = MPI.COMM_WORLD
    if comm.Get_rank() == 0:
        log_arg = args['--log']
        if log_arg == '-':
            log = sys.stdout
        else:
            if not os.path.exists(log_arg):
                dirname = os.path.dirname(log_arg)
                if dirname != '':  # If just a file name without a folder
                    os.makedirs(dirname, exist_ok=True)
            log = open(log_arg, 'w')

    exhaustive = not bool(args['--random-search'])
    # print('exhaustive =', exhaustive)
    if exhaustive and 'general' == (args.get('--preference', None)):
        raise TypeError('Exhaustive search can be performed only with single-peaked preference (till now).')

    all_previously_run = dict()  # To hold all runs from all seeds simulated on all threads
    seeds__rank = comm.Get_rank()
    seeds__num_processors = comm.Get_size()
    seeds__all_previously_run_count = 0
    seeds__run_base = seed
    seeds__run_size = int(args['--initial-run-size'])

    target_measurements = [
        ('percentage_winner_is_weak_condorcet', False), ('percentage_winner_is_strong_condorcet', False),
        ('percentage_truthful_winner_wins', False), ('percentage_of_convergence', False),
        ('average_time_to_convergence', False), ('average_social_welfare', False),
        ('stable_states_sets', True), ('winning_sets', True)
    ]

    more_work = True

    while more_work:
        seeds__chunk_size = int(math.ceil(seeds__run_size / seeds__num_processors))
        seeds__chunk_base = seeds__run_base + (seeds__rank * seeds__chunk_size)  # inclusive
        seeds__chunk_end = min((seeds__chunk_base + seeds__chunk_size), (seeds__run_base + seeds__run_size))  # excl
        # print(seeds__run_size, seeds__rank, seeds__run_base, seeds__run_size, seeds__chunk_size, seeds__chunk_base)
        if seeds__rank == 0:
            msg = f'going to start a run of {seeds__run_size} on {seeds__num_processors} batches, ' \
                f'{seeds__chunk_size} runs each'
            log.write(msg + '\n')
            log.write(f'Thread {seeds__rank} starts with seed {seeds__chunk_base} (in) to {seeds__chunk_end} (ex)\n')
            log.flush()

        for assigned_seed in range(seeds__chunk_base, seeds__chunk_end):
            out_path = os.path.join(args['--out-folder'], f'out-{assigned_seed:05}.log')
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
        if seeds__rank == 0:
            # Add all (gather new) values
            for returned_dict in buffer:  # [{seed, [measurements, ...]}, ...]
                for key in iter(returned_dict):
                    all_previously_run[key] = returned_dict[key]

            # sort results
            all_measurements_by_candidates, all_measurements_by_voters = sort_measurements(all_previously_run)

            # check for convergence
            more_work = not (
                    run_converged(all_measurements_by_candidates, seeds__all_previously_run_count, target_measurements,
                                  max_sum_abs_diffs=float(args['--conv-threshold']))
                    and
                    run_converged(all_measurements_by_voters, seeds__all_previously_run_count, target_measurements,
                                  max_sum_abs_diffs=float(args['--conv-threshold']))
            )

            if not more_work:
                # generate graph(s)
                generate_graphs(all_measurements_by_candidates, all_measurements_by_voters, target_measurements,
                                args['--out-folder'])
        else:
            more_work = None
        more_work = comm.bcast(more_work, root=0)
        # print(f'Thread {seeds__rank} more work =', more_work, flush=True)

        seeds__run_base += seeds__run_size
        seeds__run_size = int(math.ceil((seeds__run_size + seeds__all_previously_run_count) / 2))
        if seeds__rank == 0:
            seeds__all_previously_run_count = len(all_previously_run)
        seeds__all_previously_run_count = comm.bcast(seeds__all_previously_run_count, root=0)

    if seeds__rank == 0:
        log.write("Done.\n")
        log.flush()
        log.close()
        plt.show()


def run_converged(all_measurements_sorted: dict, seeds_all_previously_run_count: int, target_measurements: list,
                  max_sum_abs_diffs=0.10
                  # , extremities=0.05
                  ) -> bool:
    # print('=============================')
    if not seeds_all_previously_run_count:
        return False
    for attr_name, len_attr in target_measurements:
        for level1 in all_measurements_sorted.items():
            for level2 in level1[1].items():
                msrmnt_lst = level2[1]
                old_values = [
                    len(operator.attrgetter(attr_name)(msrmnt)) if len_attr else operator.attrgetter(attr_name)(msrmnt)
                    for msrmnt in msrmnt_lst[:seeds_all_previously_run_count]
                ]
                current_values = [
                    len(operator.attrgetter(attr_name)(msrmnt)) if len_attr else operator.attrgetter(attr_name)(msrmnt)
                    for msrmnt in msrmnt_lst
                ]
                # After much consideration, I simply decided to take the wider distribution and apply it
                # to the smaller one (the subset) keeping the same bin boundaries.
                # len_extremity = int(len(current_values) * extremities / 2)
                # old_values_barred = current_values[len_extremity: -1-len_extremity]
                # lbound = current_values[len_extremity]
                # ubound = current_values[-1 - len_extremity]

                current_hist, edges = np.histogram(current_values, bins='auto', density=True)
                # print(level1[0], level2[0], attr_name, current_values)
                # print(edges, np.diff(edges), current_hist, flush=True)
                old_hist, edges = np.histogram(old_values, bins=edges, density=True)
                diff_edges = np.diff(edges)
                # print(np.multiply(old_hist, diff_edges))
                # print(np.multiply(current_hist, diff_edges))
                subtract = np.subtract(np.multiply(old_hist, diff_edges), np.multiply(current_hist, diff_edges))
                sum_abs_diffs = np.sum(abs(subtract))
                # print(subtract, np.abs(subtract), sum_abs_diffs)
                if sum_abs_diffs > max_sum_abs_diffs:
                    return False
    else:
        print('============> Run Converged <============', flush=True)
        return True


def run_all_simulations_per_seed(args) -> list:
    """Run different candidates numbers [5-7]* different voters numbers [cmin -12]* 50 repeat

    :param args: all arguments after adjusting THIS suit seed
    :return: list of measures, one for every profile (candidates/voters/preferences)
    """
    out = args['out']
    log = args['log']
    assigned_seed = args['assigned_seed']
    utility = {
        'borda': BordaUtility(),
        'expo': ExpoUtility(base=args['<BASE>'] if args['<BASE>'] else 2,
                            exponent_step=args['<EXPO_STEP>'] if args['<EXPO_STEP>'] else  1),
    }.get(args['--utility'], None)
    cmin = int(args['--cmin'])
    cmax = int(args['--cmax'])
    # vmin = int(args['--vmin'])
    vmin = cmin if 'cmin' == args['--vmin'] else int(args['--vmin'])
    vmax = int(args['--vmax'])
    rand = random.Random(assigned_seed)
    exhaustive = not bool(args['--random-search'])  # duplicate code of the outer line
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
        # Generate deterministic list of candidates
        terminal_gap = False
        inter_gaps = True
        all_candidates = generate_candidates(n_candidates, exhaustive, rand, terminal_gap, inter_gaps)
        # print(n_candidates, all_candidates, flush=True)

        # number of n_candidates <= n_voters <= 12
        n_voters_range = range(max(vmin, n_candidates), vmax + 1)
        for n_voters in n_voters_range:
            if n_voters % 2:
                continue

            out.write(f'\n------------ voters = {n_voters}, Candidates = {n_candidates}-------------------\n')
            out.flush()
            # log.write(f'\n------------ voters = {n_voters}, Candidates = {n_candidates}-------------------\n')

            if exhaustive:
                # Generate deterministic list of voters
                # adjust bins acc to terminal and internal gaps
                terminal = 1 if terminal_gap else 0
                delta = 2 if inter_gaps else 1
                last_bin = terminal + (n_candidates * delta)
                if terminal and not inter_gaps:
                    last_bin += 1
                deterministic_list_of_voters_choices = permute_identityless(list(range(last_bin)), n_voters, False, list())
                # print('len = ', len(deterministic_list_of_voters_choices), deterministic_list_of_voters_choices, flush=True)
                

            # Use it :)
            determinant = deterministic_list_of_voters_choices[assigned_seed % len(deterministic_list_of_voters_choices)] if exhaustive else rand

            all_voters = generate_voters(n_voters, args['--voters'], utility, determinant)
            # print(all_voters, flush=True)

            # voters build their preferences
            for voter in all_voters:
                voter.build_profile(all_candidates, preference)
            # collective profile
            profile = [voter.getprofile() for voter in all_voters]
            initial_status = Status.from_profile(profile)

            # print(n_candidates, n_voters, assigned_seed, all_voters, flush=True)
            # continue  # FIXME for development purpose only
            streams = {'log': log, 'out': out}
            measurements = run_simulation_alleles(all_candidates, all_voters, initial_status, profile, rand, streams,
                                                  tie_breaking_rule, utility)
            all_profiles_measurements.append(measurements)
    return all_profiles_measurements


def run_simulation_alleles(all_candidates, all_voters, initial_status, profile, rand, streams, tie_breaking_rule,
                           utility):
    alleles = []  # Alleles are scenarios
    for run in range(50):
        scenario = run_simulation(all_candidates, all_voters, initial_status, tie_breaking_rule, rand,
                                  **streams)
        alleles.append(scenario)
    measurements = aggregate_alleles(alleles, all_voters, profile, utility, tie_breaking_rule)
    # log.write("-------measurements\n")
    # log.write(str(measurements)+'\n')
    # log.write("-------\n")
    return measurements


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
    out.flush()
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
                filter(lambda i: all_voters[i].most_recent_vote != current_status.toppers[0], active_voters_indices))
        else:
            # This condition needs to be double checked for all corner cases
            active_voters_indices = list(
                filter(lambda i: tie_breaking_rule.winning_probability(
                    current_status.toppers, all_voters[i].most_recent_vote) < (1 / n_toppers), active_voters_indices))

        status_changed = None
        # Select one voter randomly from Current active_voters_indices list
        while active_voters_indices and step < max_steps:  # Note that we check number of steps as well
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
                    out.write('\tAbstain\n')

                if active_voters_indices:
                    out.write('\n')
                else:
                    return simulation_converged(current_status, scenario, **streams)
            # elif response.frm == response.to:
            #     # voter was satisfied (currently a dead case)
            #     out.write('\n')
            else:
                out.write("<-- enhancement\n")
                # update ballot counts
                current_status.votes[response.frm] -= 1
                current_status.votes[response.to] += 1
                # then reorder candidates
                current_status.in_order()

                scenario.append(current_status.copy())
                status_changed = True
                break

        # if there were NO active voters (corner case, everyone is already satisfied with the same single candidate)
        if status_changed is None:
            # print('Corner case', len(all_candidates), len(all_voters), flush=True)
            return simulation_converged(current_status, scenario, write_converged=False, **streams)

        # Now we know we entered and exited the inner loop and are sure the active voters list was not exhausted
        if status_changed:
            # we broke from the inner loop because the last step was successful.
            # Go back to the top of outer loop to continue based on the new status
            continue  # No actual need for the keyword 'continue' here. It is just a place holder like 'pass'
        else:
            # we gracefully exited the inner loop because max steps was exhausted
            return simulation_not_converged(current_status, scenario, **streams)
    else:
        # we gracefully exited the outer loop because max steps was exhausted
        return simulation_not_converged(current_status, scenario, **streams)


def sort_measurements(all_previously_run: dict):
    temp = all_previously_run.popitem()
    seed, sample_measurements_arr = temp[0], temp[1]
    all_previously_run[seed] = sample_measurements_arr
    n_candidates_range = sorted({msrmnt.n_candidates for msrmnt in sample_measurements_arr})
    n_voters_range = sorted({msrmnt.n_voters for msrmnt in sample_measurements_arr})
    # print(n_candidates_range)
    # print(n_voters_range, flush=True)
    all_measurements_by_candidates = dict()
    all_measurements_by_voters = dict()
    for n_candidates in n_candidates_range:
        all_measurements_by_candidates[n_candidates] = dict()
        for n_voters in n_voters_range:
            if n_voters < n_candidates:
                continue
            msrmnt_arr = [msrmnt
                          for sample_measurements_arr in all_previously_run.values()
                          for msrmnt in sample_measurements_arr
                          if msrmnt.n_candidates == n_candidates and msrmnt.n_voters == n_voters]
            # measurements_summary = MeasurementsSummary.from_iterable(msrmnt_arr, n_candidates, n_voters)
            all_measurements_by_candidates[n_candidates][n_voters] = msrmnt_arr
            all_measurements_by_voters.setdefault(n_voters, dict())[n_candidates] = msrmnt_arr
    return all_measurements_by_candidates, all_measurements_by_voters


def generate_graphs(all_measurements_by_candidates: dict, all_measurements_by_voters: dict, target_measurements: list,
                    out_dir: str):
    generate_graphs_one_side(all_measurements_by_candidates, target_measurements, 'Candidates', 'Voters', 'o-', out_dir)
    generate_graphs_one_side(all_measurements_by_voters, target_measurements, 'Voters', 'Candidates', '^-', out_dir)


def generate_graphs_one_side(all_measurements_by_candidates, target_measurements, y_label: str, x_label: str,
                             mark: str, out_dir: str = './') -> None:
    for attr_name, len_attr in target_measurements:
        plt.figure()

        for level1_dict in all_measurements_by_candidates.items():
            n_level1, level2_dict = level1_dict[0], level1_dict[1]
            lst = []
            for n_level2, measurements_lst in level2_dict.items():
                attr_summary = np.average([
                    len(operator.attrgetter(attr_name)(msrmnt)) if len_attr else operator.attrgetter(attr_name)(msrmnt)
                    for msrmnt in measurements_lst])
                lst.append((n_level2, attr_summary))
            print(n_level1, lst)
            separate_x_y = list(zip(*lst))
            print("separate: ", separate_x_y)
            if separate_x_y:
                plt.plot(separate_x_y[0], separate_x_y[1], mark, label=f'{y_label} = {n_level1}')

        title = attr_name.replace('_', ' ')
        if len_attr:
            title = 'len of ' + title
        plt.title(title)
        plt.legend()
        plt.xlabel(x_label)

        filename = f'{out_dir}/{attr_name} different {y_label}.png'
        plt.savefig(filename, trnsparent=True)
        # plt.show(block=False)


def simulation_converged(last_status: Status, scenario: list, write_converged=True, **streams) -> list:
    out = streams['out']
    if write_converged:
        out.write("Converged\n")
    out.write(f'{last_status}\tFinal state\n')
    out.flush()
    scenario.append(last_status.copy())
    scenario.append(True)
    return scenario


def simulation_not_converged(last_status: Status, scenario: list, **streams) -> list:
    out = streams['out']
    out.write(f'{last_status} No convergence\n')
    out.flush()
    scenario.append(last_status.copy())
    scenario.append(False)
    return scenario


def generate_voters(n_voters: int, voter_type: str, utility: Utility, determinant):
    all_voters = []
    exhaustive = isinstance(determinant, list)
    if exhaustive:
        deterministic_list_of_voters_choices: list = determinant
        for i in range(n_voters):
            v: Voter = Voter.make_voter(voter_type, deterministic_list_of_voters_choices[i], utility)
            all_voters.append(v)
            # raise NotImplementedError("Not yet implemented")
    else:
        for i in range(n_voters):
            rand: Random = determinant
            # v: Voter = Voter.make_voter(voter_type, rand.randrange(positions_range), utility)
            v: Voter = Voter.make_voter(voter_type, rand.random(), utility)
            all_voters.append(v)
    return all_voters


def generate_candidates(n_candidates: int, exhaustive: bool, rand: Random, terminal_gap=False, inter_gaps=True):
    all_candidates = []
    if exhaustive:
        offset = 1 if terminal_gap else 0
        delta = 2 if inter_gaps else 1
        for i in range(n_candidates):
            c: Candidate = Candidate(chr(b'A'[0] + i), offset + (i * delta))
            all_candidates.append(c)
    else:
        for i in range(n_candidates):
            # c: Candidate = Candidate(chr(b'A'[0] + i), i+1)
            c: Candidate = Candidate(chr(b'A'[0] + i), rand.random())
            all_candidates.append(c)
    return all_candidates


# --------------------------
if __name__ == '__main__':
    main()
