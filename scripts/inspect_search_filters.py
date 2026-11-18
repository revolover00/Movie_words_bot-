"""Inspect public search form controls without sending messages."""
from html.parser import HTMLParser
from urllib.request import urlopen

class Controls(HTMLParser):
    def __init__(self):
        super().__init__(); self.controls = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('select', 'input', 'form'):
            self.controls.append(f"{tag} {attrs}")

with urlopen('https://clip.cafe/', timeout=30) as response:
    parser = Controls()
    parser.feed(response.read().decode('utf-8', 'replace'))
    print('::notice title=Search controls::' + ' | '.join(parser.controls))
