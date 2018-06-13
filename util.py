import os
import shutil
import random
from datetime import datetime
import time
import sys


sample_size = None
min_freq = 0
reorder = True
enabled_deps = 'all'
pair_method = 'outside'
metric = None
n_pairs = 50
quarters = [1]
remove_args = 'none'
per_source = False

cats = ['avalanche', 'cold_wave', 'drought', 'earthquake', 'flood', 'heat_wave', 'landslide', 'sinkhole', 'tornado',
        'hurricane', 'tsunami', 'volcano', 'wildfire']


def set_sample_size(k):
    global sample_size
    sample_size = k if k is None or k > 0 else None


def set_min_freq(c):
    global min_freq
    min_freq = c


def set_enabled_deps(d):
    global enabled_deps
    enabled_deps = d


def set_pair_method(m):
    global pair_method
    pair_method = m


def set_seed(seed):
    random.seed(seed)


def set_reorder(r):
    global reorder
    reorder = r


def set_per_source(s):
    global per_source
    per_source = s


def set_metric(m):
    global metric
    metric = m


def set_n_pairs(n):
    global n_pairs
    n_pairs = n


def set_quarters(q):
    global quarters
    quarters = q


def set_remove_args(r):
    global remove_args
    remove_args = r


def global_dir(parent, add_metric=False):
    k = sample_size if sample_size is not None else 'none'
    t = 'yes' if reorder else 'no'

    subdir = '{}_{}_{}_{}_{}'.format(k, min_freq, enabled_deps, pair_method, t)
    if add_metric:
        subdir = '{}_'.format(metric) + subdir
    out_dir = os.path.join(parent, subdir)
    return out_dir


def sample(docs, k=None, labels=None, verbose=False):
    global sample_size
    if k is None:
        k = sample_size

    if k is not None and k < len(docs):
        if labels is not None:
            if len(labels) != len(docs):
                log('Length of labels list not equal to doc list: {} != {}'.format(len(labels), len(docs)))
            else:
                labeled = {}
                for doc, label in zip(docs, labels):
                    if label not in labeled:
                        labeled[label] = [doc]
                    else:
                        labeled[label].append(doc)

                total_sample = []
                print('Downsampling per label:')
                for label, label_docs in labeled.items():
                    print(' > {}: '.format(label), end='')
                    label_sample = sample(label_docs, k=k, verbose=True)
                    total_sample += label_sample

                print('sampled down from {} to {}\n'.format(len(docs), len(total_sample)))
                return total_sample

        if verbose:
            print('sampled down from {} to {}'.format(len(docs), k))
        return random.choices(docs, k=k)
    if verbose:
        print('not sampled down size {}'.format(len(docs)))
    return docs


def backup_dir(path):
    os.makedirs('backups', exist_ok=True)
    new_path = 'backups/' + path + '-{}'

    i = 1
    while os.path.isdir(new_path.format(i)):
        i += 1

    shutil.move(path, new_path.format(i))


def ensure_empty_dir(path, enter=False):
    if os.path.isdir(path):
        try:
            os.removedirs(path)
        except OSError as e:
            backup_dir(path)

    os.makedirs(path)
    if enter:
        os.chdir(path)


def log(text, cat='debug'):
    os.makedirs('log', exist_ok=True)
    with open('log/{}.txt'.format(cat), 'a') as f:
        f.write('[{}] {}\n'.format(datetime.now(), text))


class Progressbar:
    def __init__(self, total=1):
        self.i = 0
        self.total = total
        self.starttime = time.time()

    def update(self, i):
        self.i = i
        percent = self.i / self.total * 100
        per60 = int(self.i / self.total * 60)
        s_remaining = round((time.time() - self.starttime) / self.i * (self.total - self.i))
        eta = '{}m {}s'.format(s_remaining // 60, s_remaining % 60)

        print('[ {:60} ] {:.2f}% [{}/{}] {} remaining'.format('#' * per60, percent, self.i, self.total, eta), end='\r')

    def remove(self):
        width = 92 + len(str(self.i)) + len(str(self.total))
        print(' ' * width, end='\r')


def load_sauri_lexicon_verbs():
    verb_deps = set()

    lex_path = os.path.join(sys.path[0], 'data', 'Sauri-lexicon-tabformat.txt')
    with open(lex_path) as f:
        for line in f:
            kind, pos, word, deps = line.rstrip().split('\t')
            if kind != 'stop' and pos == 'Verb':
                for dep in deps.split(' '):
                    verb_deps.add((word, dep))
                verb_deps.add((word, 'ROOT'))

    return verb_deps
