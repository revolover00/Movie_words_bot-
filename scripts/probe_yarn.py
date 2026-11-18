"""Probe public movie-clip sources without sending bot messages."""
import re
import urllib.request
from urllib.error import HTTPError

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
urls = {
    'ClipCafe search': 'https://clip.cafe/?s=Nice+to+meet+you&usersearch=1&ss=s',
    'ClipCafe clip': 'https://clip.cafe/3-ninjas-kick-back-1994/hello-s2100/t/4',
    'Yarn search': 'https://yarn.co/yarn-find?text=curious&type=movies',
}
for name, url in urls.items():
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as r:
            text = r.read(500000).decode('utf-8', 'replace')
            media = re.findall(r'.{0,100}(?:\.mp4|\.m3u8).{0,150}', text, re.I)
            result = f'{r.status}; bytes={len(text)}; media={media[:2]}'
    except Exception as exc:
        result = f'{type(exc).__name__}: {exc}'
    result = result.replace('%', '%25').replace('\n', '%0A').replace('\r', '%0D')
    print(f'::notice title={name}::{result[:2000]}')
