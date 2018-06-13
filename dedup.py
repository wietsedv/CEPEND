from glob import glob
import os


def run():
    os.chdir('plaintext')

    known_ids = {}

    dup_counter = 0
    files = glob('*/*.txt')
    for filepath in files:
        cat, filename = filepath.split('/')
        if cat != 'unrelated':
            if filename in known_ids.keys():
                known_ids[filename].append(cat)
                dup_counter += 1
            else:
                known_ids[filename] = [cat]

    print('Removing dupplicate documents...', end='\r')

    for filename, cats in known_ids.items():
        if len(cats) > 1:
            minority, min_count = '', 10000
            for cat in cats:
                count = len(os.listdir(cat))
                if count < min_count:
                    minority, min_count = cat, count

            for cat in cats:
                if cat != minority:
                    os.remove(os.path.join(cat, filename))
