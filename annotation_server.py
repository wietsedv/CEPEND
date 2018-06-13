from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import random
from glob import glob
import urllib
import sys


page = """
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{
    margin: 0;
    padding: 10px;
    font-family: arial;
}}
.container {{
    max-width: 450px;
    margin: 10px auto;
}}
h2 {{
    text-align: center;
}}
.pair-wrapper {{
    border: 1px solid #ccc;
    background-color: #fafafa;
    border-radius: 4px;
    padding: 20px 0;
}}
.event-wrapper {{
    padding: 10px 0;
}}
.event-wrapper:after {{
    display: block;
    content: " ";
    clear: both;
}}

.subj {{
    text-align: right;
    font-style: italic;
    width: 30%;
}}
.event {{
    text-transform: uppercase;
    font-weight: 600;
    text-align: center;
    width: 40%;
}}
.obj {{
    text-align: left;
    font-style: italic;
    width: 30%;
}}
.subj, .event, .obj {{
    display: block;
    float: left;
    min-height: 10px;
}}
.arrow {{
    display: block;
    text-align: center;
}}

form {{
    margin-top: 20px;
    text-align: center;
}}

form button {{
    border: none;
    color: white;
    padding: 15px 32px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 10px;
    cursor: pointer;
    width: 200px;
}}
form button.green {{
    background-color: #4CAF50;
    float: left;
    font-weight: bold;
}}
form button.red {{
    background-color: #F44336;
    float: right;
}}
form button.yellow {{
    background-color: #ffaa00;
    float: none;
    margin-top: 20px;
}}
</style>
</head>
<body>
Hello {}. You have annotated {}/{} available event pairs.<br /><br />

<h2>Natural Disaster events</h2>

<div class="container">
    <div class="pair-wrapper">
    <div class="event-wrapper">
        <span class="subj">{}</span><span class="event">{}</span><span class="obj">{}</span>
    </div>
    <div class="event-wrapper">
        <span class="arrow">&#x25BC;</span>
    </div>
    <div class="event-wrapper">
        <span class="subj">{}</span><span class="event">{}</span><span class="obj">{}</span>
    </div>
    </div>

    <form method="post">
        <input type="hidden" name="meta" value="{}">

        <button type="submit" name="annotation" value="correct" class="green">Contingent</button>
        <button type="submit" name="annotation" value="wrong" class="red">Not Contingent</button>
        <button type="submit" name="annotation" value="correct-reversed" class="yellow">
            Contingent, but wrong order
        </button>
    </form>
</div>

<h3>Rules for annotation:</h3>
<ul>
<li>Two events are described: the bold uppercase verbs.</li>
<li>The optional arguments left and right are example subjects and objects: actors and reactors.</li>
<li>Follow these instructions:
<ul>
    <li>A shown event pair is contingent if the occurrence of the first event influences the occurrence of
        the second event.</li>
    <li>The first event does not have to directly cause the second event, but the occurrence of the first event
        should make the second event more likely.</li>
    <li>If the subject and object arguments are given, they should be used as context.</li>
    <li>If the subject and object do not make sense together, choose one.</li>
    <li>If no arguments are given, imagine your own realistic context.</li>
    <li>If additional context is needed, remember that the domain is <i>Natural Disasters</i>.</li>
</ul>
</li>
</ul>
</body>
</html>
"""


pair_metas = set()
for filepath in glob('ranked_pairs/*/all-[1-4].csv'):
    with open(filepath) as f:
        for line in f:
            meta = tuple(line.rstrip().split(';')[:6])
            pair_metas.add(meta)


def load_annotations(annotator):
    known_pairs = set()
    filename = 'annotations/{}.csv'.format(annotator)
    if os.path.isfile(filename):
        with open(filename) as f:
            for line in f:
                meta = tuple(line.rstrip().split(';')[:-1])
                known_pairs.add(meta)

    return known_pairs


def save_annotation(annotator, post_data):
    global known_annotations

    filename = 'annotations/{}.csv'.format(annotator)
    meta, annotation = post_data['meta'][0], post_data['annotation'][0]
    with open(filename, 'a') as f:
        f.write('{};{}'.format(meta, annotation) + '\n')

    if annotator not in known_annotations:
        known_annotations[annotator] = load_annotations(annotator)
    known_annotations[annotator].add(tuple(meta.split(';')))


def random_pair(annotated=set()):
    available_pairs = pair_metas - annotated
    if len(available_pairs) == 0:
        return None
    return random.sample(available_pairs, 1)[0]


known_annotations = {}


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global known_annotations

        if self.path != '/' and not self.path.startswith('/annotator='):
            return

        self.send_response(200)

        self.send_header('Content-type', 'text/html')
        self.end_headers()

        if self.path == '/':
            content = 'Vraag Wietse (<a href="mailto:w.de.vries.21@student.rug.nl">w.de.vries.21@student.rug.nl</a>) \
                       om een persoonlijke URL.'
            self.wfile.write(bytes(content, 'utf8'))
        elif self.path.startswith('/annotator='):
            annotator = self.path.replace('/annotator=', '')
            if annotator:
                if annotator not in known_annotations:
                    known_annotations[annotator] = load_annotations(annotator)

                annotations = known_annotations[annotator]
                pair_meta = random_pair(known_annotations[annotator])
                if pair_meta is None:
                    self.wfile.write(bytes('You have annotated all event pairs! Thanks!', 'utf8'))
                    return
                e1, e2, subj1, obj1, subj2, obj2 = pair_meta
                meta_str = ';'.join(pair_meta)
                self.wfile.write(bytes(page.format(annotator.capitalize(), len(annotations), len(pair_metas),
                                       subj1, e1, obj1, subj2, e2, obj2, meta_str), 'utf8'))

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        post_data = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))

        annotator = self.path.replace('/annotator=', '')
        if annotator:
            save_annotation(annotator, post_data)

        self.do_GET()


print('starting server')
host = (sys.argv[1], 80) if len(sys.argv) > 1 else ('localhost', 8080)
httpd = HTTPServer(host, RequestHandler)
print('running server')
httpd.serve_forever()
