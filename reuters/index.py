import subprocess
import util

keywords = ['avalanche', 'cold wave', 'drought', 'quake', 'flood', 'heat wave', 'landslide', 'sinkhole',
            'tornado', 'hurricane', 'tsunami', 'volcan', 'wildfire']

command = 'grep -nlri --include \*.xml ../data/reuters -e "{}" > index/{}.txt'


def run():
    util.ensure_empty_dir('index')

    total_docs_count = 0

    for i, cat in enumerate(keywords):
        print('Indexing {}...'.format(util.cats[i]), end='\r')
        subprocess.call(command.format(cat, util.cats[i].replace(' ', '\ ')), shell=True)

        with open('index/{}.txt'.format(util.cats[i])) as f:
            docs_count = sum(1 for _ in f)
            total_docs_count += docs_count
            print('Indexed {} - {} documents'.format(util.cats[i], docs_count))
