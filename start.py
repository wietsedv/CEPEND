#!/usr/bin/env python3

import argparse
import time
import os
import sys
import importlib
import util


available_datadirs = ['wiki', 'wikinews', 'reuters']

data_dep_action_names = ['index', 'download', 'totext']
general_action_names = ['dedup', 'events']
global_action_names = ['event_pairs', 'rank_pairs']
available_actions = data_dep_action_names + general_action_names + global_action_names

default_action_range = [available_actions[0], available_actions[-1]]

pair_deps = ['all', 'root', 'clause-root', 'best']
pair_methods = ['adjacent', 'within', 'outside']
metrics = ['pmi', 'cp', 'scp']


def get_actions(actions):
    if len(actions) != 2:
        return actions

    if actions[0] == '-':
        actions[0] = available_actions[0]
    if actions[1] == '-':
        actions[1] = available_actions[-1]

    i1, i2 = available_actions.index(actions[0]), available_actions.index(actions[1])
    return available_actions[i1:i2+1]


def parse_args():
    parser = argparse.ArgumentParser(description='CEPEND: Contingent Event Pair Extractor for Natural Disasters')

    parser.add_argument('-d', type=str, nargs='+', choices=available_datadirs, default=available_datadirs,
                        help='List of data collection to use. (default: %(default)s)')
    parser.add_argument('-f', type=str,  help=argparse.SUPPRESS)

    parser.add_argument('-a', type=str, nargs='+', choices=available_actions + ['-', 'test'],
                        default=default_action_range, help='Actions to perform. \
                        When 2 items are given, all intermediate actions are also performed. (default: %(default)s)')

    parser.add_argument('-k', type=int, default=-1,
                        help='Max # documents per category per data collection [events step].')

    parser.add_argument('-c', type=int, default=10,
                        help='Min event pair frequency [event_pairs step] (default: %(default)s)')
    parser.add_argument('-p', type=str, default='all', choices=pair_deps,
                        help='Pair dependencies [event_pairs step] (default: %(default)s)')
    parser.add_argument('-m', type=str, default='outside', choices=pair_methods,
                        help='Pair method [event_pairs step] (default: %(default)s)')
    parser.add_argument('--reorder', const=True, default=False, dest='reorder', nargs='?', metavar='',
                        help='Set all pairs in most probable order with TemProb [event_pairs step]')
    parser.add_argument('--per-source', const=True, default=False, dest='per_source', nargs='?', metavar='',
                        help='Enable event pair extraction per source [event_pairs step]')

    parser.add_argument('-e', type=str, default=None, choices=metrics,
                        help='Event pair ranking metric [rank_pairs step]')
    parser.add_argument('-n', type=int, default=50,
                        help='How many event pairs to save (per quarter) [rank_pairs step]')
    parser.add_argument('-q', type=int, nargs='+', default=[1], choices=[1, 2, 3, 4],
                        help='Which quarters of ranked list to save [rank_pairs step]')
    parser.add_argument('-r', type=str, default='none', choices=['all', 'even', 'odd', 'none'],
                        help='Remove argument information for event pairs. [rank_pairs step] (default: %(default)s)')

    parser.add_argument('-s', type=int, default=None, help='Random seed')

    args = parser.parse_args()

    util.set_sample_size(args.k)
    util.set_min_freq(args.c)
    util.set_enabled_deps(args.p)
    util.set_pair_method(args.m)
    util.set_reorder(args.reorder)
    util.set_per_source(args.per_source)
    util.set_metric(args.e)
    util.set_n_pairs(args.n)
    util.set_quarters(args.q)
    util.set_remove_args(args.r)
    util.set_seed(args.s)

    if args.f is not None:
        parts = args.f.split('/')
        if len(parts) > 1 and parts[-1].endswith('.py'):
            datadirs, action = [parts[-2]], parts[-1].replace('.py', '')
            if action not in available_actions:
                print('Action \'{}\' cannot be run.'.format(action), file=sys.stderr)
                exit(-1)
            if datadirs[0] not in available_datadirs:
                datadirs = args.d
            return datadirs, [action]
        else:
            print('File \'{}\' cannot be run.'.format(args.f), file=sys.stderr)
            exit(-1)

    return args.d, get_actions(args.a)


def time_diff(start_time):
    return divmod(round(time.time() - start_time), 60)


def run_action(datadir, module):
    if module in data_dep_action_names:
        module = datadir + '.' + module

    importlib.import_module(module).run()


enabled_dirs, enabled_actions = parse_args()

print('CEPEND: Contingent Event Pair Extractor for Natural Disasters')
print('By Wietse de Vries, 2018, University of Groningen')
print()
print('enabled data sources: {}'.format(', '.join(enabled_dirs)))
print('enabled actions:      {}'.format(', '.join(enabled_actions)))
print('event pair method:    {}'.format(util.pair_method))
print('enabled dependencies: {}'.format(util.enabled_deps))
print('sample size per cat:  {}'.format('all' if util.sample_size is None else util.sample_size))
print('min pair frequency:   {}'.format(util.min_freq))
print('reorder events:       {}'.format('yes' if util.reorder else 'no'))
print('list per source:      {}'.format('yes' if util.per_source else 'no'))
print('used ranking metric:  {}'.format(util.metric))
print()

data_path = os.getcwd()
if 'test' in enabled_actions:
    print('#### Testing pair methods and metrics #### ')
    util.set_temprob(False)

    print('## Preparing test data')
    os.chdir(os.path.join(data_path, 'test_data'))
    run_action('test_data', 'events')

    os.chdir(data_path)
    import event_pairs

    for method in pair_methods:
        util.set_pair_method(method)
        for deps in pair_deps:
            util.set_enabled_deps(deps)

            print('\n# Method: {}, Dependencies: {}'.format(method, deps))
            event_pairs.run(['test_data'])

            ok = True
            with open('event_pairs/test_data.csv') as real_file:
                with open('test_data/gold_event_pairs/{}-{}.csv'.format(method, deps)) as gold_file:
                    for real_line, gold_line in zip(real_file.readlines(), gold_file.readlines()):
                        if real_line != gold_line:
                            ok = False
                            print('"{}" should be "{}"'.format(real_line.strip(), gold_line.strip()))
            if ok:
                print('Seems OK!')
            else:
                print('Test failed')
    exit(0)

for datadir in enabled_dirs:
    print('#### Processing {} #### '.format(datadir))
    start_time = time.time()

    i, total_i = 0, len(enabled_actions)
    for action in enabled_actions:
        if action in global_action_names:
            break

        os.chdir(os.path.join(data_path, datadir))

        action_start_time = time.time()
        i += 1
        print('## Step {}/{}: {}'.format(i, total_i, action))

        run_action(datadir, action)

        print('\n> took {}m, {}s\n'.format(*time_diff(action_start_time)))

    print('finished! It took {}m, {}s\n'.format(*time_diff(start_time)))


os.chdir(data_path)
if 'event_pairs' in enabled_actions:
    print('#### Collecting event pair info in all event files #### ')
    action_start_time = time.time()

    import event_pairs
    event_pairs.run(enabled_dirs)

    print('\n> took {}m, {}s\n'.format(*time_diff(action_start_time)))

os.chdir(data_path)
if 'rank_pairs' in enabled_actions:
    print('#### Ranking pairs by metric #### ')
    action_start_time = time.time()

    import rank_pairs
    rank_pairs.run()

    print('\n> took {}m, {}s\n'.format(*time_diff(action_start_time)))
