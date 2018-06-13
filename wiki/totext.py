from glob import glob
import json
import os
import re
import util


sectionsplit = re.compile('((\n)+(==.*?==)?)+((\n)+|$)')


def format_content(content):
    return sectionsplit.sub('\n\n', content)


def validate_subcategories(pageid, title, cats):
    global flood_control_count, dams_count, works_about_count, films_about_count

    for cat in cats:
        if cat.startswith('Flood control in'):
            util.log('{} [{}]: FLOOD CONTROL'.format(pageid, title), 'totext-subcats')
            return False
        if cat.startswith('Dams in'):
            util.log('{} [{}]: DAMS'.format(pageid, title), 'totext-subcats')
            return False
        if cat.startswith('Works about'):
            util.log('{} [{}]: WORKS ABOUT'.format(pageid, title), 'totext-subcats')
            return False
        if cat.startswith('Films about'):
            util.log('{} [{}]: FILMS ABOUT'.format(pageid, title), 'totext-subcats')
            return False
        if cat == 'Dust Bowl':
            util.log('{} [{}]: DUST BOWL'.format(pageid, title), 'totext-subcats')
            return False
    return True


def normalize(pageid, props):
    title, content = props['title'], props['content']

    if title.startswith('List of '):
        util.log('{} [{}]: LIST OF'.format(pageid, title), 'totext-content')
    elif title.startswith('Template:'):
        util.log('{} [{}]: TEMPLATE'.format(pageid, title), 'totext-content')
    elif title.startswith('Book:'):
        util.log('{} [{}]: BOOK'.format(pageid, title), 'totext-content')
    elif not validate_subcategories(pageid, title, props['subcats']):
        return False, False
    else:
        content = format_content(content)
        if len(content) >= 10:
            return title, content
        util.log('{} [{}]: CONTENT LENGTH {}'.format(pageid, title, len(content)), 'totext-content')

    return False, False


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
            title, content = normalize(filename, props)

            if title:
                with open(output_filename, 'w', encoding='utf-8') as output_f:
                    output_f.write(title + '\n\n')
                    output_f.write(content)
            else:
                removed_count += 1
        total_count += 1

    percent = round(removed_count/total_count * 100)
    print('Converted documents. Removed {}/{} docs [{}%]'.format(removed_count, total_count, percent))
