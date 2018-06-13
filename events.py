"""
Reads $source/plaintext and creates csv's with events in $source/events

Format:
doc_id;section_nr;sentence_nr;verb_lemma;subj_lemma;obj_lemma;dep
"""

import os
import spacy
import util


nlp = None
sauricon_verb_deps = None


def update_args(features, token):
    subj_tags = ['nsubj', 'agent']
    obj_tags = ['obj', 'dobj', 'nsubjpass']

    if token.is_stop:
        return

    subj_index = subj_tags.index(features['subj'].dep_) if features['subj'] is not None else None
    obj_index = obj_tags.index(features['obj'].dep_) if features['obj'] is not None \
        and features['obj'].dep_ in obj_tags else None

    token_dep = token.dep_
    if token_dep in subj_tags and (subj_index is None or subj_tags.index(token_dep) < subj_index):
        features['subj'] = token
    elif token_dep in obj_tags and (obj_index is None or obj_tags.index(token_dep) < obj_index):
        features['obj'] = token


def get_argument(token):
    if token is None:
        return ''

    if token.pos_ == 'PRON' or token.ent_type_ == 'PERSON':
        return 'person'
    elif token.ent_type_ == 'ORG':
        return 'organization'
    elif token.ent_type_ == 'GPE':
        return 'country'
    elif token.ent_type_ == 'LANGUAGE':
        return 'language'
    elif token.ent_type_ == 'DATE':
        return 'date'
    elif token.ent_type_ == 'TIME':
        return 'time'
    elif token.ent_type_ == 'MONEY':
        return 'money'
    elif token.ent_type_ == 'QUANTITY':
        return 'quantity'
    elif token.ent_type_ == 'ORDINAL':
        return 'number'
    elif token.ent_type_ == 'CARDINAL':
        return 'number'

    return token.lemma_


def parse_section(doc):
    events = []

    for i, sent in enumerate(doc.sents):
        for verb in sent:
            if verb.tag_[0:2] != 'VB' or verb.dep_.startswith('aux'):
                continue
            if (not verb.is_alpha) or verb.is_stop or verb.lemma_ == 'be':
                continue
            if (verb.lemma_, verb.dep_) in sauricon_verb_deps:
                continue

            args = {
                'subj': None,
                'obj': None,
            }

            if verb.dep_.endswith('mod'):
                args['obj'] = verb.head

            for token in verb.children:
                update_args(args, token)

            subj, obj = get_argument(args['subj']), get_argument(args['obj'])
            events.append([i, verb.lemma_, subj, obj, verb.dep_])

    if len(events) < 2:
        return []

    return events


def generate_text_sections(cat, files):
    file_ids, sections = [], []

    for filename in files:
        file_id = filename.replace('.txt', '')
        filepath = 'plaintext/{}/{}'.format(cat, filename)
        with open(filepath) as input_f:
            input_f.readline().rstrip()  # = title
            input_f.readline().rstrip()

            section = ''
            for line in input_f.readlines():
                if line.strip() == '':
                    if section != '':
                        if section.isupper():
                            section = section.lower()
                        file_ids.append(file_id)
                        sections.append(section.rstrip())
                        section = ''
                else:
                    section += line

            if section != '':
                if section.isupper():
                    section = section.lower()
                file_ids.append(file_id)
                sections.append(section.rstrip())

    return file_ids, sections


def chunks(l, chunk_size):
    for i in range(0, len(l), chunk_size):
        yield l[i:i + chunk_size]


def append_to_file(cat, events):
    if len(events) == 0:
        return

    event_dir = 'events-{}'.format(util.sample_size if util.sample_size is not None else 'none')
    filename = '{}/{}.csv'.format(event_dir, cat)
    with open(filename, 'a', encoding='utf-8') as output_f:
        for event in events:
            output_f.write(';'.join([str(prop) for prop in event]) + '\n')


def run():
    global nlp, sauricon_verb_deps
    nlp = spacy.load('en')
    sauricon_verb_deps = util.load_sauri_lexicon_verbs()

    util.ensure_empty_dir('events-{}'.format(util.sample_size if util.sample_size is not None else 'none'))

    for cat in util.cats:
        files = [fname for fname in os.listdir('plaintext/{}'.format(cat)) if not fname.startswith('.')]
        files = util.sample(files)

        bar = util.Progressbar(len(files))
        f_count, e_count = 0, 0

        print('Extracting events about {} (sample size: {} files)...'.format(cat, util.sample_size), end='\r')

        for files_chunk in chunks(files, chunk_size=20):
            file_ids, sections = generate_text_sections(cat, files_chunk)
            docs = nlp.pipe(sections)

            current_file_id, events, i = None, [], 0
            for file_id, doc in zip(file_ids, docs):
                if file_id != current_file_id:
                    i = 0
                    e_count += len(events)
                    append_to_file(cat, events)
                    current_file_id, events = file_id, []

                events = events + [[file_id, i] + parse for parse in parse_section(doc)]
                i += 1

            e_count += len(events)
            append_to_file(cat, events)

            f_count += len(files_chunk)
            bar.update(f_count)

        bar.remove()
        print('Extracted events about {} from {} files - {} events'.format(cat, f_count, e_count))
