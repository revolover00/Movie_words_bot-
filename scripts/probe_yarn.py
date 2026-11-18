"""Probe Yarn search and an example video without contacting Telegram or the database."""
import re
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MovieWordBot/1.0)"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=25) as response:
        return response.read(), response.headers.get_content_type()

try:
    search, _ = get('https://yarn.co/yarn-find?text=curious&type=movies')
    ids = list(dict.fromkeys(re.findall(r'/yarn-clip/([0-9a-f-]{36})', search.decode('utf-8', 'replace'))))
    if not ids:
        raise ValueError('search returned no clip IDs')
    page, _ = get('https://yarn.co/yarn-clip/' + ids[0])
    html = page.decode('utf-8', 'replace')
    urls = re.findall(r'https?[^\s"\'<>\\]+\.mp4(?:\?[^\s"\'<>\\]*)?', html)
    if not urls:
        raise ValueError('clip page has no MP4 URL')
    data, content_type = get(urls[0].replace('&amp;', '&'))
    if len(data) < 1024 or not (content_type.startswith('video/') or b'ftyp' in data[:64]):
        raise ValueError(f'not a valid MP4 response: {content_type}, {len(data)} bytes')
    print(f'::notice title=Yarn probe::Search returned {len(ids)} clips; MP4 downloaded ({len(data)} bytes, {content_type}).')
except Exception as exc:
    print(f'::error title=Yarn probe failed::{type(exc).__name__}: {str(exc)[:300]}')
    raise

# Exercise the same exact-phrase matching and MP4 downloader used by the job.
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from yarn_clips import find_clip

with TemporaryDirectory() as folder:
    for expression in ('Nice to meet you', 'That makes sense', 'I owe you one'):
        try:
            clip = find_clip(expression, Path(folder))
            print(f'::notice title=Phrase probe::{expression}: matched and downloaded {clip.title}')
        except Exception as exc:
            print(f'::error title=Phrase probe failed::{expression}: {type(exc).__name__}: {exc}')
            raise
