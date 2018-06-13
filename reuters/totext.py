from glob import glob
import json
import os
import util


def normalize(pageid, title, content, cat, topics):
    if title is None:
        title = ''
    if content is None:
        content = ''
    if topics is None:
        topics = []

    # if cat == 'unrelated':
    #     return title, content, True

    cat = cat.lower()
    if cat == 'volcano':
        cat = 'volcan'
    if cat == 'earthquake':
        cat = 'quake'
    if '_' in cat:
        cat = cat.replace('_', ' ')

    if 'GDIS' not in topics:
        util.log('{} [{}]: NOT GDIS but {}'.format(pageid, title, '/'.join(topics)), 'badcontent')
    elif len(content) < 10:
        util.log('{} [{}]: CONTENT LENGTH {}'.format(pageid, title, len(content)), 'badcontent')
    elif cat not in title.lower() and content.lower().count(cat) < 2:
        util.log('{} [{}]: CAT COUNT [{}]'.format(pageid, title, cat), 'badcontent')
    else:
        return title, content, True

    return title, content, False


def run():
    util.ensure_empty_dir('plaintext')

    print('Converting documents to plaintext...', end='\r')

    total_count, removed_count = 0, 0
    for input_filename in glob('raw/*/*.txt'):
        _, cat, filename = input_filename.split('/')

        output_dir = 'plaintext/{}'.format(cat)
        os.makedirs(output_dir, exist_ok=True)
        output_filename = '{}/{}'.format(output_dir, filename)

        with open(input_filename) as input_f:
            props = json.load(input_f)
            title, content, valid = normalize(filename, props['title'], props['content'], cat, props['topics'])

            if valid:
                with open(output_filename, 'w', encoding='utf-8') as output_f:
                    output_f.write(title + '\n\n')
                    output_f.write(content)
            else:
                removed_count += 1
        total_count += 1

    percent = round(removed_count/total_count * 100)
    print('Converted documents. Removed {}/{} docs [{}%]'.format(removed_count, total_count, percent))
