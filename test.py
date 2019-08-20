import itertools
import math
import queue
from queue import Queue
from random import Random
import time

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
    ln = rand.randint(10, 20)
    for i in range(ln):
        ret.append((i, rand.randint(2, 5)))
    return ret


def do_task(task):
    task_id, task_time = task
    print(f'task {task_id} will sleep {task_time} sec.', flush=True)
    time.sleep(task_time)
    print(f'                        {task_id} done.', flush=True)


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

    rank = comm.Get_rank()
    master = rank == 0
    if master:
        print('version = ', MPI.Get_version())
        print('lib version = ', MPI.Get_library_version())
        # share parameters
        args = docopt(doc, version='0.1.0')
        # print(args)
        # TODO seed ?
        seed = int(args['--seed'])
        # generate universal list of tasks
        global_tasks = prepare_list_of_tasks()
        more_work = len(global_tasks) > 0
    else:
        args = None
        global_tasks = None
        more_work = None

    # share the list somehow
    global_tasks = comm.bcast(global_tasks, root=0)
    args = comm.bcast(args, root=0)
    more_work = comm.bcast(more_work, root=0)
    q = Queue()

    if master:
        free_processors = [i for i in range(1, comm.Get_size())]
        busy_processors = []
        print(free_processors, flush=True)
        while more_work:
            # list available processors and each processor's global_tasks
            n_processors = len(free_processors)
            default_load = math.ceil(len(global_tasks)/n_processors)  # TODO int?
            assigned_tasks = {(p_id, tuple(global_tasks[(p_id - 1) * default_load: p_id * default_load]))
                              for p_id in free_processors}
            print(assigned_tasks, flush=True)

            # send the commands to do
            requests = []
            # for each node
            for pid, p_tasks in assigned_tasks:
                # Send the the command to do list of global_tasks or task IDs
                req = comm.isend(('Run', p_tasks), pid)
                requests.append(req)
            busy_processors, free_processors = free_processors, busy_processors
            MPI.Request.waitall(requests)
            print('Main Thread finished sending. Will wait for responses.', flush=True)

            # wait for FREE signals
            while more_work:
                feed_back = comm.recv()
                if feed_back[0] == 'FREE':
                    free_processor_id = int(feed_back[1])
                    busy_processors.remove(free_processor_id)
                    free_processors.append(free_processor_id)
                    print(f'Processor {free_processor_id} is FREE.', flush=True)
                # for each finish signal
                #   ask all nodes for their loads (or receive their frequent updates [and results ?])
                #   find the most loaded one
                #   ask it to stop at half of its current default_load
                #   check and calculate its default_load again (to avoid rat race)
                #   send the new default_load (half of prev default_load) to the free processor
                # update more_work
                more_work = len(busy_processors)

            print('All finished. Exiting.')
            for pid in free_processors:
                comm.isend(('STOP', ), dest=pid)
                print(f'STOP sent to {pid:2}', flush=True)

    else:
        # while more_work:
        while more_work:
            # receive signal
            req = comm.irecv(source=0)
            msg = req.wait()
        #   if signal is parameters:
        #       receive parameters
        #       receive (or generate ?) the list of global_tasks
            # if signal is start command:
            command = msg[0]
            if command == 'Run':
                # receive the tasks /task IDs
                p_tasks = msg[1]
                # put them all in the queue
                for task in p_tasks:
                    q.put(task)
                # TODO fork another thread:
                while q.qsize() != 0:
                    do_task(q.get())
                    # send a finished task signal (and result ?)
                # send "FREE" signal
                comm.send(('FREE', rank), dest=0)
            elif command == 'STOP':
                print(f'STOP received at {rank}', flush=True)
                more_work = False
        #   elif signal is CHANGE command:
        #       put lock on list(s)
        #       set last to LIMIT
        #       release lock


if __name__ == '__main__':
    main()