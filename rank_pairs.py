import pandas as pd
import csv
import os
import util


def run():
    if util.metric is None:
        util.set_metric('pmi')
        run()
        util.set_metric('scp')

    util.ensure_empty_dir(util.global_dir('ranked_pairs', True))

    for filename in os.listdir(util.global_dir('event_pairs')):
        if not filename.endswith('.csv'):
            continue

        input_path = os.path.join(util.global_dir('event_pairs'), filename)
        output_path = os.path.join(util.global_dir('ranked_pairs', True), filename)

        pairs_names = ['event1', 'event2', 'subj1', 'obj1', 'subj2', 'obj2', 'frequency',
                       'pmi', 'scp', 'cp', 'typicality']
        pairs_df = pd.read_csv(input_path, sep=';', names=pairs_names, index_col=['event1', 'event2'],
                               quoting=csv.QUOTE_NONE, encoding='utf-8')
        pairs_df.sort_values(util.metric, ascending=False, inplace=True)

        q_size = len(pairs_df) / 4
        for i in util.quarters:
            with open(output_path.replace('.csv', '-{}.csv'.format(i)), 'w') as f:
                p = int((i - 1) * q_size)
                for j, row in enumerate(pairs_df.iloc[p:p+util.n_pairs].iterrows(), start=1):
                    index, meta = row
                    e1, e2 = index
                    meta.fillna('', inplace=True)
                    if (j % 2 == 0 and util.remove_args in ('all', 'even')) \
                            or (j % 2 == 1 and util.remove_args in ('all', 'odd')):
                        meta['subj1'], meta['obj1'], meta['subj2'], meta['obj2'] = '', '', '', ''

                    row = ';'.join(['{}'] * 10)
                    pmi = round(meta['pmi'], 3)
                    scp = round(meta['scp'], 3)
                    cp = round(meta['cp'], 3)
                    typ = round(meta['typicality'], 3)
                    f.write(row.format(e1, e2, meta['subj1'], meta['obj1'], meta['subj2'], meta['obj2'],
                                       pmi, scp, cp, typ) + '\n')

        print('Ranked {} by {}. Saved to {}'.format(filename, util.metric, util.global_dir('ranked_pairs', True)))
