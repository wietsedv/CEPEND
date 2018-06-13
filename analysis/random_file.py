import sys
import os
import numpy as np
import json
from collections import defaultdict
import spacy

nlp = spacy.load('en')

source = sys.argv[1]
cat = sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 1

os.chdir(os.path.join(sys.path[0], '..', source))


def print_raw_meta(cat, doc_id):
    with open('raw/{}/{}.txt'.format(cat, doc_id)) as f:
        data = json.load(f)

        title = data['title']
        if source == 'wiki':
            print('https://en.wikipedia.org/wiki/{}'.format(title.replace(' ', '_')))
        elif source == 'wikinews':
            print('https://en.wikinews.org/wiki/{}'.format(title.replace(' ', '_')))
        else:
            print(title)

        print('')
        if source in ['wiki', 'wikinews']:
            print('Categories:    ' + ', '.join(data['cats']))
            print('\nCat hierarchy: ' + ', '.join(data['subcats']))
        else:
            print('Topics:    ' + ', '.join(data['topics']))
        print('')


def get_random_section_events(cat, doc_id):
    events = {}
    with open('events/{}.csv'.format(cat)) as f:
        for line in f.readlines():
            parts = line.strip().split(';')
            curr_doc_id, section_nr, sent_nr = parts[0], int(parts[1]), int(parts[2])

            if curr_doc_id == doc_id:
                if section_nr not in events:
                    events[section_nr] = defaultdict(list)
                events[section_nr][sent_nr].append(parts[3:])
            elif len(events) > 0:
                break

    if len(events) == 0:
        return None, {}

    section_nr = np.random.choice(list(events.keys()))
    print('> Section {} of [{}]\n'.format(section_nr, ','.join(str(nr) for nr in events.keys())))
    return section_nr, events[section_nr]


def print_plaintext(cat, doc_id, section_nr, events):
    with open('plaintext/{}/{}.txt'.format(cat, doc_id)) as f:
        f.readline()
        f.readline()

        sect_nr, sent_nr = 0, 0
        for line in f.readlines():
            if line.strip() == '':
                sect_nr += 1

            if section_nr is None:
                continue
            elif sect_nr == section_nr:
                for sent in nlp(line.strip()).sents:
                    print('[{}] {}'.format(sent_nr, sent.text))
                    for event, subj, obj, dep in events[sent_nr]:
                        print(' ' * (len(str(sent_nr)) + 3) + '{:>10} {:^10} {:<10} [{}]'.format(
                            subj, event.upper(), obj, dep))
                    sent_nr += 1
                    print('')
            elif sect_nr > section_nr:
                break


for filename in np.random.choice(os.listdir('plaintext/{}'.format(cat)), size=n):
    print('#' * 80)
    doc_id = filename.replace('.txt', '')

    print_raw_meta(cat, doc_id)

    section_nr, events = get_random_section_events(cat, doc_id)
    print_plaintext(cat, doc_id, section_nr, events)

    print('')
