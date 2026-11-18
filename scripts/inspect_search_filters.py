from html.parser import HTMLParser
from urllib.request import Request, urlopen
class Controls(HTMLParser):
    def __init__(self):
        super().__init__(); self.field = None; self.items = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'select': self.field = attrs.get('name')
        if tag == 'option' and self.field in ('audio', 'sl', 'type'): self.items.append(f"{self.field}:{attrs.get('value')}")
    def handle_endtag(self, tag):
        if tag == 'select': self.field = None
with urlopen(Request('https://clip.cafe/', headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}), timeout=30) as response:
    parser = Controls(); parser.feed(response.read().decode('utf-8', 'replace'))
    print('::notice title=Search controls::' + ' | '.join(dict.fromkeys(parser.items)))
