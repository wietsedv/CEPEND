import os
import json
import util


def run():
    util.ensure_empty_dir('raw')

    for cat in util.cats:
        print('Moving docs about {}...'.format(cat), end='\r')

        index_filename = 'index/{}.txt'.format(cat)
        output_dir = 'raw/{}'.format(cat)
        os.makedirs(output_dir)

        i = 0
        with open(index_filename) as index_f:
            for line in index_f.readlines():
                input_filename = line.rstrip()

                disk, date, filename = input_filename.split('/')[-3:]
                output_filename = output_dir + '/' + filename.replace('newsML.xml', '.txt')

                import xml.etree.ElementTree as ET
                root = ET.parse(input_filename).getroot()

                title = root.find('./headline').text
                text = root.findall('./text/p')
                content = '\n'.join([p.text for p in text])

                topic_codes = root.findall('metadata/codes[@class="bip:topics:1.0"]/code')
                topics = [code.attrib['code'] for code in topic_codes]

                with open(output_filename, 'w') as output_f:
                    json.dump({
                        'title': title,
                        'content': content,
                        'topics': topics
                    }, output_f)

                i += 1

        print('Moved docs about {} - {} documents'.format(cat, i))
