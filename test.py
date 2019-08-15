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


def prepare_list_of_tasks():
    ret = []
    rand = Random()
    ln = rand.randint(10, 30)
    for i in range(ln):
        ret.append((i, rand.randint(50, 2000)))
    return ret


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

    comm = MPI.COMM_WORLD
    master = comm.Get_rank() == 0
    if master:
        # share parameters
        args = docopt(doc, version='0.1.0')
        # print(args)
        # TODO seed ?
        seed = int(args['--seed'])
        # generate universal list of tasks
        tasks = prepare_list_of_tasks()
        more_work = len(tasks) > 0
    else:
        args = None
        tasks = None
        more_work = None

    # share the list somehow
    tasks = comm.bcast(tasks, root=0)
    args = comm.bcast(args, root=0)
    more_work = comm.bcast(more_work, root=0)

    if master:
        free_processors = [range(1, comm.Get_size()+1)]
        while more_work:
            # list available processors and each processor's tasks
            n_processors = len(free_processors)
            load = len(tasks)/n_processors
            assigned_tasks = {(p_id, tasks[(p_id - 1) * load: p_id* load]) for (p_id) in free_processors}
            print(assigned_tasks, flush=True)
            # send the command to do
            # for each node
            #   send the the command to do N tasks
            #   send its list of tasks or task IDs

            # wait for FREE signals
            # for each finish signal
            #   ask all nodes for their loads (may replace this with receiving their frequent updates [and results ?])
            #   find the most loaded one
            #   ask it to stop at half of its current load
            #   check and claculate its load again (to avoid rat race)
            #   send the new load (half of prev load) to the free processor
            # update more_work
            pass
    else:
        # while more_work:
        #   receive signal
        #   if signal is parameters:
        #       receive parameters
        #       receive (or generate ?) the list of tasks
        #   if signal is start command:
        #       receive command to do N Tasks
        #       receive the task IDs
        #       start worker thread:
        #          for each task
        #               [DO THE TASKS]
        #               send a finished task signal (and result ?)
        #               update internal lists (shall it be B4 sending signal [and results] ?)
        #           send "FREE" signal
        #   if signal is CHANGE command:
        #       put lock on list(s)
        #       set last to LIMIT
        #       release lock
        #   if signal is STOP command:
        #       update more_work.
        #       congratulations!
        pass


if __name__ == '__main__':
    main()