import pandas as pd
import csv
import sys
import os

os.chdir(os.path.join(sys.path[0], '..'))

for source in ['wiki', 'wikinews', 'reuters']:
    print('#### {}'.format(source.capitalize()))

    events_df = pd.read_csv('{}/event_pairs/events-all.csv'.format(source), sep=';', names=['event', 'subj', 'obj', 'frequency'], index_col='event', quoting=csv.QUOTE_NONE, encoding='utf-8')
    pairs_df = pd.read_csv('{}/event_pairs/all.csv'.format(source), sep=';', names=['event1', 'event2', 'frequency', 'pmi', 'cp', 'scp'], index_col=['event1', 'event2'], quoting=csv.QUOTE_NONE, encoding='utf-8')

    print('## Events')
    print(events_df.head(10))
    print('[...]\n')
    print(events_df.describe())
    print('\n\n## Pairs')
    print(pairs_df.head(10))
    print('[...]\n')
    print(pairs_df.describe())

    print('\n')
