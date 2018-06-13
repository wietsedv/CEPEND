import requests
import util


api_url = 'https://en.wikipedia.org/w/api.php?action=query&format=json&list=categorymembers&cmlimit=500\
&cmprop=ids|title|type'
random_url = 'https://en.wikipedia.org/w/api.php?action=query&format=json&generator=random&grnnamespace=0&grnlimit=500'

known_categories = set()
wiki_cats = ['Avalanches', 'Cold_waves', 'Droughts', 'Earthquakes', 'Floods', 'Heat_waves',
             'Landslides', 'Sinkholes', 'Tornadoes', 'Tropical cyclones', 'Tsunamis',
             'Volcanic_events', 'Wildfires']


def get_pages(url, depth=0, subcats=[]):
    r = requests.get(url)
    result_json = r.json()

    if result_json['batchcomplete'] != '':
        util.log('Incomplete download of index {}'.format(url), 'errors')

    members = result_json['query']['categorymembers']
    pages = {}
    for i, meta in enumerate(members):
        if meta['type'] == 'page' and depth > 1:
            pages[meta['pageid']] = (meta['title'], subcats)
        elif meta['type'] == 'subcat' and meta['pageid'] not in known_categories and \
                (depth > 0 or ' by ' in meta['title']):
            known_categories.add(meta['pageid'])
            util.log('-'*depth + ' {}/{} [{}]'.format(i, len(members), meta['title']), 'wiki-categories')

            new_pages = get_pages(api_url + '&cmpageid={}'.format(meta['pageid']), depth+1,
                                  subcats=subcats+[meta['title']])
            pages = {**pages, **new_pages}

    return pages


def get_random_pages(n=0):
    p = 0
    pages = {}
    while p < n:
        r = requests.get(random_url)
        result_json = r.json()

        if result_json['batchcomplete'] != '':
            util.log('Incomplete download of index {}'.format(random_url), 'errors')

        for meta in result_json['query']['pages'].values():
            if meta['pageid'] not in pages:
                pages[meta['pageid']] = meta['title']
                p += 1
            if p >= n:
                break

    return pages


def run():
    global known_categories

    util.ensure_empty_dir('index')

    total_page_count = 0

    for i, cat in enumerate(wiki_cats):
        known_categories = set()

        print('Indexing {}...'.format(util.cats[i]), end='\r')

        pages = get_pages(api_url + '&cmtitle=Category:{}'.format(cat), subcats=[cat])
        filename = 'index/{}.csv'.format(util.cats[i])
        with open(filename, 'w') as f:
            pagerows = []
            for pageid, meta in pages.items():
                title, subcats = meta
                pagerows.append('{};{};{}'.format(pageid, title, '/'.join(subcats)))

            f.write('\n'.join(pagerows))

        print('Indexed {} - {} documents'.format(util.cats[i], len(pages)))
        total_page_count += len(pages)
