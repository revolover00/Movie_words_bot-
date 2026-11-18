"""Inspect public search form controls without sending messages."""
from html.parser import HTMLParser
from urllib.request import urlopen, Request

class Controls(HTMLParser):
    def __init__(self):
        super().__init__(); self.controls = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('select', 'input', 'form'):
            self.controls.append(f"{tag} {attrs}")

with urlopen(Request('https://clip.cafe/', headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}), timeout=30) as response:
    parser = Controls()
    parser.feed(response.read().decode('utf-8', 'replace'))
    print('::notice title=Search controls::' + ' | '.join(parser.controls))
