"""Check Yarn public search and clip endpoints without sending bot messages."""
import urllib.error
import urllib.request

urls = {
    'search': 'https://yarn.co/yarn-find?text=curious&type=movies',
    'getyarn-search': 'https://getyarn.io/yarn-find?text=curious&type=movies',
    'memes-search': 'https://memes.yarn.co/yarn-find?text=curious&type=movies',
    'clip': 'https://yarn.co/yarn-clip/305c386b-5828-4421-b5ee-372687117294',
    'media': 'https://y.yarn.co/305c386b-5828-4421-b5ee-372687117294.mp4',
}
headers = {'User-Agent': 'Mozilla/5.0 (compatible; MovieWordBot/1.0)'}
for name, url in urls.items():
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
            data = r.read(65536)
            result = f'{r.status} content-type={r.headers.get_content_type()} bytes={len(data)} final={r.url.split("?")[0]}'
    except Exception as exc:
        result = f'{type(exc).__name__}: {exc}'
    print(f'::notice title=Yarn {name}::{result}')
