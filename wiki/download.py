import requests
import os
import asyncio
import json
import util


api_url = 'https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts|categories&explaintext&exlimit=1\
&pageids={}'


async def download_page(sem, path, pageid, title, subcats, bar):
    await sem.acquire()

    try:
        r = requests.get(api_url.format(pageid))
        props = r.json()['query']['pages'][pageid]
        with open(os.path.join(path, pageid + '.txt'), 'w') as f:
            json.dump({
                'title': props['title'],
                'content': props['extract'],
                'subcats': subcats,
                'cats': [cat['title'].replace('Category:', '') for cat in props['categories']]
            }, f)
    except Exception as e:
        util.log('Downloading of {} > {} [{}] failed. retrying: {}'.format(path, pageid, title, e), 'download')
        await download_page(sem, path, pageid, title, subcats, bar)

    bar.update(bar.i + 1)
    sem.release()


async def download_all(cat):
    index_filename = 'index/{}.csv'.format(cat)
    output_dir = 'raw/{}'.format(cat)
    os.makedirs(output_dir)

    sem = asyncio.Semaphore(15)
    tasks = set()
    bar = util.Progressbar()

    print('Loading index of {}...'.format(cat), end='\r')

    i = 0
    with open(index_filename) as f:
        for line in f.readlines():
            i += 1
            pageid, title, subcats = line.split(';', maxsplit=2)
            subcats = [subcat.replace('Category:', '') for subcat in subcats.rstrip().split('/')]
            tasks.add(download_page(sem, output_dir, pageid, title, subcats, bar))

    print('Downloading docs about {}...'.format(cat), end='\r')
    bar.total = i

    done, pending = await asyncio.wait(tasks)

    bar.remove()
    print('Downloaded docs about {} - {} documents'.format(cat, i))


def run():
    util.ensure_empty_dir('raw')

    loop = asyncio.new_event_loop()

    for cat in util.cats:
        loop.run_until_complete(download_all(cat))

    loop.close()
