import util
from collections import Counter
from math import log
import numpy as np
from collections import defaultdict
import os
import sys


all_event_meta = defaultdict(list)
temprob_counts, total_temprob_count = None, None


def count_freq(e1, e2, pair_counts, both=False):
    count = 0
    if (e1, e2) in pair_counts:
        count = pair_counts[(e1, e2)]
        if not isinstance(count, int):
            count = count[0]
    if both:
        count += count_freq(e2, e1, pair_counts)

    return count


def scp(e1, e2, event_counts, pair_counts):
    e1e2_count = count_freq(e1, e2, pair_counts, both=True)
    if e1e2_count < util.min_freq:
        return 0
    p_e1e2 = e1e2_count / (event_counts[e2] + 1)
    p_e2e1 = e1e2_count / (event_counts[e1] + 1)
    return p_e1e2 * p_e2e1


def pmi(e1, e2, event_counts, pair_counts, num_events, num_pairs):
    e1e2_count = count_freq(e1, e2, pair_counts, both=True)
    p_e1e2 = e1e2_count / num_pairs
    p_e1 = np.int64(event_counts[e1]) / num_events
    p_e2 = np.int64(event_counts[e2]) / num_events
    if e1e2_count >= util.min_freq and p_e1 > 0 and p_e2 > 0:
        return log(p_e1e2 / (p_e1 * p_e2))
    else:
        return 0


def cp(e1, e2, pair_counts, num_pairs, pmi_score):
    if count_freq(e1, e2, pair_counts) == 0:
        return 0
    p_e1e2 = (count_freq(e1, e2, pair_counts) + 1) / num_pairs
    p_e2e1 = (count_freq(e2, e1, pair_counts) + 1) / num_pairs
    return pmi_score + log(p_e1e2 / p_e2e1)


def typicality(e1, e2, pair_counts, num_pairs):
    global temprob_counts, total_temprob_count
    if temprob_counts is None:
        temprob_counts = Counter()
        total_temprob_count = 0
        with open(os.path.join(sys.path[0], 'data/TemProb.txt')) as f:
            for line in f:
                parts = line.strip().split('\t')
                v1, v2, count = parts[0][0:-3], parts[1][0:-3], int(parts[3])
                temprob_counts[(v1, v2)] += count
                total_temprob_count += count

    p_real = (count_freq(e1, e2, pair_counts, True) + 1) / num_pairs
    p_temprob = (count_freq(e1, e2, temprob_counts, True) + 1) / total_temprob_count
    return log(p_real / p_temprob)


def best_attrs(attrs):
    subjs, objs = zip(*attrs)
    subjs = [subj for subj in subjs if subj]
    objs = [obj for obj in objs if obj]
    if len(subjs) == 0:
        subjs = ['']
    if len(objs) == 0:
        objs = ['']
    return max(set(subjs), key=subjs.count), max(set(objs), key=objs.count)


def add_pairs(prev_events, new_event, prev_metas, new_meta, pair_meta):
    if new_event is None:
        return
    for prev_event, prev_meta in zip(prev_events, prev_metas):
        if prev_event != new_event:
            pair_meta[(prev_event, new_event)].append((prev_meta[0:2], new_meta[0:2]))


def best_dep_event(events, metas):
    if len(metas) == 0:
        return None, None

    i = 0
    deps = [meta[2] for meta in metas]
    if 'ROOT' in deps:
        i = deps.index('ROOT')
    elif 'ccomp' in deps:
        i = deps.index('ccomp')
    elif 'advcl' in deps:
        i = deps.index('advcl')
    elif 'xcomp' in deps:
        i = deps.index('xcomp')
    elif 'conj' in deps:
        i = deps.index('conj')

    return events[i], metas[i]


def read_event_pairs(cat, datadir=None):
    global all_event_meta
    pair_meta = defaultdict(list)

    event_dir = 'events-{}'.format(util.sample_size if util.sample_size is not None else 'none')
    filepath = '{}/{}.csv'.format(event_dir, cat)
    if datadir is not None:
        filepath = os.path.join(datadir, filepath)

    if not os.path.isfile(filepath) or (util.enabled_deps == 'best' and util.pair_method != 'outside'):
        return pair_meta

    with open(filepath) as input_f:
        prev_events, prev_metas = [], []
        curr_events, curr_metas = [], []
        curr_doc_id, curr_section_nr, curr_sent_nr = None, None, None

        for line in input_f:
            parts = line.rstrip().split(';')
            if len(parts) != 7:
                util.log('Invalid line: ' + line.rstrip())
                continue

            doc_id, section_nr, sent_nr, event, subj, obj, dep = parts

            # Check allowed dependencies
            if util.enabled_deps == 'root' and dep != 'ROOT':
                continue
            elif util.enabled_deps == 'clause-root' and dep not in ('ROOT', 'xcomp', 'conj'):
                continue

            # Add pairs according to specified method
            if doc_id == curr_doc_id and section_nr == curr_section_nr:
                if util.pair_method == 'adjacent':
                    add_pairs(curr_events, event, curr_metas, (subj, obj, dep), pair_meta)
                elif util.pair_method == 'within':
                    if sent_nr == curr_sent_nr:
                        add_pairs(curr_events, event, curr_metas, (subj, obj, dep), pair_meta)
                    else:
                        curr_events, curr_metas = [], []
                elif util.pair_method == 'outside':
                    if util.enabled_deps == 'best':
                        if sent_nr != curr_sent_nr:
                            best_event, best_meta = best_dep_event(curr_events, curr_metas)
                            add_pairs(prev_events, best_event, prev_metas, best_meta, pair_meta)

                            curr_events, curr_metas = [], []
                            prev_events, prev_metas = [best_event], [best_meta]
                    else:
                        if sent_nr != curr_sent_nr:
                            prev_events, prev_metas = curr_events, curr_metas
                            curr_events, curr_metas = [], []
                        add_pairs(prev_events, event, prev_metas, (subj, obj, dep), pair_meta)
            else:
                if util.enabled_deps == 'best':
                    best_event, best_meta = best_dep_event(curr_events, curr_metas)
                    add_pairs(prev_events, best_event, prev_metas, best_meta, pair_meta)

                curr_events, curr_metas = [], []
                prev_events, prev_metas = [], []

            if util.pair_method == 'adjacent':
                curr_events, curr_metas = [], []

            curr_events.append(event)
            curr_metas.append((subj, obj, dep))
            all_event_meta[event].append((subj, obj))

            curr_doc_id, curr_section_nr, curr_sent_nr = doc_id, section_nr, sent_nr

    return pair_meta


def order_by_temprob(pairs):
    global temprob_counts, total_temprob_count
    temprob_counts = Counter()
    total_temprob_count = 0

    all_pairs = set(pairs)
    for e1, e2 in pairs:
        all_pairs.add((e2, e1))

    sorted_pairs = sorted(all_pairs)
    orders = defaultdict(int)

    with open(os.path.join(sys.path[0], 'data/TemProb.txt')) as f:
        for line in f:
            parts = line.strip().split('\t')
            v1, v2, rel, count = parts[0][0:-3], parts[1][0:-3], parts[2], int(parts[3])
            temprob_counts[(v1, v2)] += count
            total_temprob_count += count

            for i, pair in enumerate(sorted_pairs):
                e1, e2 = pair
                if e1 < v1:
                    del sorted_pairs[i]
                elif e1 > v1:
                    break
                else:
                    if e2 < v2:
                        del sorted_pairs[i]
                    elif e2 > v2:
                        break
                    else:
                        if rel == 'before':
                            orders[(e1, e2)] += count
                        elif rel == 'after':
                            orders[(e1, e2)] -= count
                        break
    return orders


def filter_pairs(pair_meta, keep_all=False, reorder=True):
    if not util.reorder:
        reorder = False

    pair_counts = {pair: len(meta) for pair, meta in pair_meta.items()}
    temprob_order = order_by_temprob(pair_meta.keys()) if reorder else None

    print('Finding best subjects and objects', end='\r')
    best_metas = {e: best_attrs(meta) for e, meta in all_event_meta.items()}

    filtered_event_counts, filtered_pair_counts = Counter(), {}
    total_events, total_pairs = 0, 0

    for pair, metas in pair_meta.items():
        e1, e2 = pair
        meta1, meta2 = zip(*metas)

        pair_counts.setdefault((e2, e1), 0)
        count = pair_counts[(e1, e2)]

        if reorder:
            e1e2 = pair_counts[(e1, e2)] * temprob_order[(e1, e2)]
            e2e1 = pair_counts[(e2, e1)] * temprob_order[(e2, e1)]
            temp_order = e1e2 - e2e1
            if temp_order != 0:
                e1, e2, meta1, meta2 = (e1, e2, meta1, meta2) if temp_order > 0 else (e2, e1, meta2, meta1)
            elif pair_counts[(e1, e2)] == pair_counts[(e2, e1)]:
                e1, e2, meta1, meta2 = (e1, e2, meta1, meta2) if e1 < e2 else (e2, e1, meta2, meta1)
            else:
                e1, e2, meta1, meta2 = (e1, e2, meta1, meta2) if pair_counts[(e1, e2)] > pair_counts[(e2, e1)] else \
                                       (e2, e1, meta2, meta1)
            count += pair_counts[(e2, e1)]

        if (e1, e2) not in filtered_pair_counts:
            if count >= util.min_freq:
                e1_meta, e2_meta = best_metas[e1], best_metas[e2]
                filtered_pair_counts[(e1, e2)] = (count, *e1_meta, *e2_meta)
                filtered_event_counts[e1] += count
                filtered_event_counts[e2] += count
                total_events += 2 * count
                total_pairs += count
            elif keep_all:
                filtered_pair_counts[(e1, e2)] = (count, '', '', '', '')

    return filtered_event_counts, filtered_pair_counts, total_events, total_pairs


def load_unrelated_event_counts(source='.'):
    unrelated_counts = Counter()
    event_dir = 'events-{}'.format(util.sample_size if util.sample_size is not None else 'none')

    with open(os.path.join(source, event_dir, 'unrelated.csv')) as f:
        for line in f:
            event = line.split(';')[3]
            unrelated_counts[event] += 1

    return unrelated_counts


def save_pair_info(name, pair_meta, unrelated_counts={}, keep_all=False, reorder=True):
    print('Reordering events for {}...        '.format(name), end='\r')
    event_counts, pair_counts, total_event_count, total_pair_count = filter_pairs(pair_meta, keep_all, reorder)
    # total_unrelated_count = sum(unrelated_counts.values())

    print('Calculating scores for {}...        '.format(name), end='\r')
    with open(os.path.join(util.global_dir('event_pairs'), '{}.csv'.format(name)), 'w') as f:
        for pair, count_meta in pair_counts.items():
            e1, e2 = pair
            count, subj1, obj1, subj2, obj2 = count_meta

            pmi_score = pmi(e1, e2, event_counts, pair_counts, total_event_count, total_pair_count)
            cp_score = cp(e1, e2, pair_counts, total_pair_count, pmi_score)
            scp_score = scp(e1, e2, event_counts, pair_counts)
            typ_score = typicality(e1, e2, pair_counts, total_pair_count)

            pair_info = e1, e2, subj1, obj1, subj2, obj2, count, pmi_score, scp_score, cp_score, typ_score
            f.write(';'.join(str(prop) for prop in pair_info) + '\n')

    return len(event_counts), len(pair_counts)


def run(datadirs=(None), per_cat=False):
    util.ensure_empty_dir(util.global_dir('event_pairs'))
    all_pair_meta = defaultdict(list)

    for datadir in datadirs:
        dir_pair_meta = defaultdict(list)

        for cat in util.cats:
            print('Counting events about {}...        '.format(cat), end='\r')
            pair_meta = read_event_pairs(cat, datadir)

            if len(pair_meta) == 0:
                continue

            for e, meta in pair_meta.items():
                dir_pair_meta[e] += meta

            if per_cat:
                name = cat if datadir is None else datadir + '-' + cat
                e_count, p_count = save_pair_info(name, pair_meta)
                print('Found {} unique events and {} unique pairs about {}'.format(e_count, p_count, cat))

        if util.per_source:
            e_count, p_count = save_pair_info(datadir, dir_pair_meta, keep_all=True)
            print('Found {} unique events and {} unique pairs in {} with min freq {}'.format(
                e_count, p_count, datadir, util.min_freq))

        for e, meta in dir_pair_meta.items():
            all_pair_meta[e] += meta

    if len(datadirs) > 1:
        print('Calculating global scores...', end='\r')
        e_count, p_count = save_pair_info('all', all_pair_meta)
        print('Found {} unique events and {} unique pairs with min freq {}'.format(e_count, p_count, util.min_freq))
