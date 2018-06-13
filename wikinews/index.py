import requests
import util


api_url = 'https://en.wikinews.org/w/api.php?action=query&format=json&list=categorymembers&cmlimit=500\
&cmprop=ids|title|type'
search_url = 'https://en.wikinews.org/w/api.php?action=query&format=json&list=search&srlimit=500&srprop='
random_url = 'https://en.wikinews.org/w/api.php?action=query&format=json&generator=random&grnnamespace=0&grnlimit=500'

known_categories = set()
wikinews_cats = ['Avalanches', '#"cold wave"', '#drought', 'Earthquakes', 'Floods', '#"heat wave"', 'Mudslides',
                 '#sinkhole', 'Tornadoes', 'Tropical cyclones', 'Tsunamis', 'Volcano', 'Natural disasters&Fires']


def get_pages(url, subcats=[]):
    r = requests.get(url)
    result_json = r.json()

    if result_json['batchcomplete'] != '':
        util.log('Incomplete download of index {}'.format(url), 'errors')

    members = result_json['query']['categorymembers'] if 'categorymembers' in result_json['query'] else \
        result_json['query']['search']
    pages = {}
    for i, meta in enumerate(members):
        page_type = meta['type'] if 'type' in meta else 'page'
        if page_type == 'page':
            pages[meta['pageid']] = (meta['title'], subcats)
        elif page_type == 'subcat' and meta['pageid'] not in known_categories:
            known_categories.add(meta['pageid'])
            util.log('{}/{} [{}]'.format(i, len(members), meta['title']), 'wiki-categories')

            new_pages = get_pages(api_url + '&cmpageid={}'.format(meta['pageid']), subcats=subcats+[meta['title']])
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


def save_pages(filename, pages):
    with open(filename, 'w') as f:
        pagerows = []
        for pageid, meta in pages.items():
            title, subcats = meta
            pagerows.append('{};{};{}'.format(pageid, title, '/'.join(subcats)))

        f.write('\n'.join(pagerows))


def run():
    global known_categories

    util.ensure_empty_dir('index')

    total_page_count = 0

    for i, cat in enumerate(wikinews_cats):
        known_categories = set()
        filename = 'index/{}.csv'.format(util.cats[i])

        print('Indexing {}...'.format(util.cats[i]), end='\r')

        pages = None
        for subcat in cat.split('&'):
            if cat.startswith('#'):
                term = cat[1:]
                subpages = get_pages(search_url + '&srsearch={}+incategory:Disasters_and_accidents\
                |Natural_disasters'.format(term), subcats=['Disasters'])
            else:
                subpages = get_pages(api_url + '&cmtitle=Category:{}'.format(subcat), subcats=[subcat])
            if pages is None:
                pages = subpages
            else:
                pages = {key: pages[key] for key in pages.keys() & subpages.keys()}

        save_pages(filename, pages)

        print('Indexed {} - {} documents'.format(util.cats[i], len(pages)))
        total_page_count += len(pages)
