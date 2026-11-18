"""Inspect ClipCafe search and download connectivity without sending messages."""
import re
import urllib.request

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as r:
        return r.read(1000000), r.headers.get_content_type()
try:
    search, _ = get('https://clip.cafe/?s=Nice+to+meet+you&usersearch=1&ss=s')
    page = search.decode('utf-8', 'replace')
    for marker in ('hello-s2100', 'Nice to meet you.'):
        index = page.find(marker)
        text = page[max(0,index-350):index+1000] if index >= 0 else 'not found'
        print('::notice title=Snippet '+marker+'::'+text.replace('%','%25').replace('\n','%0A').replace('\r','%0D')[:1900])
    page, _ = get('https://clip.cafe/3-ninjas-kick-back-1994/hello-s2100/t/4')
    text = page.decode('utf-8', 'replace')
    for tag in re.findall(r'<meta[^>]+(?:og:video|og:title|og:description)[^>]*>', text, re.I)[:7]:
        print('::notice title=Clip metadata::'+tag.replace('%','%25'))
    data, typ = get('https://clip.cafe/videos/hello-s2100.mp4')
    print(f'::notice title=Media probe::type={typ} bytes={len(data)} ftyp={b"ftyp" in data[:64]}')
except Exception as exc:
    print(f'::error title=ClipCafe probe failed::{type(exc).__name__}: {exc}')
    raise
