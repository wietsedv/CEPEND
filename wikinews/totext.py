import json
import os
import re
import util


sectionsplit = re.compile('((\n)+(==.*?==)?)+((\n)+|$)')


def format_content(content):
    return sectionsplit.sub('\n\n', content)


def normalize(pageid, props):
    title, content = props['title'], format_content(props['content'])
    if len(content) >= 10:
        return title, content
    util.log('{} [{}]: CONTENT LENGTH {}'.format(pageid, title, len(content)), 'totext-content')

    return False, False


def run():
    util.ensure_empty_dir('plaintext')

    print('Converting documents to plaintext...', end='\r')

    total_count, removed_count = 0, 0
    for cat in util.cats:
        output_dir = 'plaintext/{}'.format(cat)
        os.makedirs(output_dir)

        for filename in os.listdir('raw/{}'.format(cat)):
            output_filename = '{}/{}'.format(output_dir, filename)

            with open('raw/{}/{}'.format(cat, filename)) as input_f:
                props = json.load(input_f)
                title, content = normalize(filename, props)

                if content:
                    with open(output_filename, 'w', encoding='utf-8') as output_f:
                        output_f.write(title + '\n\n')
                        output_f.write(content)
                else:
                    removed_count += 1
            total_count += 1

    percent = round(removed_count/total_count * 100)
    print('Converted documents. Removed {}/{} docs [{}%]'.format(removed_count, total_count, percent))
