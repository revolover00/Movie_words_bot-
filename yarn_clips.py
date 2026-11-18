"""Find a movie quote containing a word and download its short Yarn clip."""
from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

log = logging.getLogger(__name__)
BASE = 'https://yarn.co'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; MovieWordBot/1.0)'}
CLIP_ID = re.compile(r'/yarn-clip/([0-9a-f-]{36})(?:["\'/#?]|$)', re.I)
MP4_URL = re.compile(r'https://[^\s"\'<>\\]+\.mp4(?:\?[^\s"\'<>\\]*)?', re.I)
TITLE = re.compile(r'<title[^>]*>(.*?)</title>', re.I | re.S)
MAX_BYTES = 20 * 1024 * 1024

@dataclass(frozen=True)
class YarnClip:
    clip_id: str
    title: str
    quote: str
    url: str
    path: Path


def _get(url: str, **kwargs):
    response = requests.get(url, headers=HEADERS, timeout=(10, 30), **kwargs)
    response.raise_for_status()
    return response


def _parse_title(page: str, word: str) -> tuple[str, str] | None:
    match = TITLE.search(page)
    if not match:
        return None
    parts = [html.unescape(p).strip() for p in match.group(1).split('|')]
    if len(parts) < 4 or parts[0].upper() != 'YARN':
        return None
    quote, title = parts[1:3]
    if not re.search(rf'(?<!\w){re.escape(word)}(?!\w)', quote, re.I):
        return None
    return quote, title


def find_clip(word: str, out_dir: Path = Path('clips')) -> YarnClip:
    """Find a quote matching the whole word; never use an unrelated fallback."""
    response = _get(f'{BASE}/yarn-find', params={'text': word, 'type': 'movies'})
    ids = list(dict.fromkeys(CLIP_ID.findall(response.text)))[:20]
    for clip_id in ids:
        url = f'{BASE}/yarn-clip/{clip_id}'
        try:
            page = _get(url).text
            parsed = _parse_title(page, word)
            if not parsed:
                continue
            match = MP4_URL.search(html.unescape(page))
            if not match:
                continue
            video_url = match.group(0)
            host = urlparse(video_url).hostname or ''
            if host != 'yarn.co' and not host.endswith('.yarn.co'):
                continue
            with _get(video_url, stream=True) as video:
                final = urlparse(video.url)
                if final.scheme != 'https' or not (final.hostname == 'yarn.co' or (final.hostname or '').endswith('.yarn.co')):
                    raise ValueError('unexpected video host')
                out_dir.mkdir(parents=True, exist_ok=True)
                path = out_dir / f'yarn-{clip_id}.mp4'
                size = 0
                try:
                    with path.open('wb') as f:
                        for chunk in video.iter_content(65536):
                            size += len(chunk)
                            if size > MAX_BYTES:
                                raise ValueError('Yarn video exceeds size limit')
                            f.write(chunk)
                    with path.open('rb') as f:
                        header = f.read(64)
                    if size < 1024 or b'ftyp' not in header:
                        raise ValueError('Yarn returned invalid MP4 data')
                except Exception:
                    path.unlink(missing_ok=True)
                    raise
            quote, title = parsed
            log.info('Selected Yarn clip %s: %s', clip_id, title)
            return YarnClip(clip_id, title, quote, url, path)
        except (requests.RequestException, ValueError, OSError) as exc:
            log.warning('Could not use Yarn clip %s: %s', clip_id, exc)
    raise RuntimeError(f'No downloadable movie clip with the word {word!r} found on Yarn')
