"""Search public Clip.Cafe movie dialogue and download a matching clip."""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError

BASE = 'https://clip.cafe/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
MAX_BYTES = 20 * 1024 * 1024
log = logging.getLogger(__name__)

@dataclass(frozen=True)
class Clip:
    clip_id: str
    title: str
    quote: str
    url: str
    path: Path

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.meta = {}
        self.audio_languages = {}
        self.current_link = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'picture' and attrs.get('data-link'):
            self.current_link = attrs['data-link']
            self.links.append(self.current_link)
        audio = attrs.get('aria-label', '')
        if self.current_link and audio.startswith('Audio: '):
            self.audio_languages[self.current_link] = {x.strip().casefold() for x in audio[7:].split(',')}
        if tag == 'meta' and attrs.get('property') and attrs.get('content'):
            self.meta[attrs['property']] = attrs['content']


def get(url):
    return urlopen(Request(url, headers=HEADERS), timeout=30)


def page(url):
    with get(url) as response:
        data = response.read(2_000_000).decode('utf-8', 'replace')
    parser = PageParser()
    parser.feed(data)
    return parser


def matches(phrase: str, quote: str) -> bool:
    """Require all expression words in order, ignoring punctuation and case."""
    def tokenize(text: str) -> list[str]:
        # Fold Latin accents but preserve combining marks in scripts where
        # they are essential to meaning (e.g. Hindi vowel signs).
        result, current = [], []
        latin = False
        for char in unicodedata.normalize('NFKD', text.casefold()):
            if unicodedata.category(char).startswith('M'):
                if current and not latin:
                    current.append(char)
            elif char.isalnum():
                current.append(char)
                latin = 'LATIN' in unicodedata.name(char, '')
            elif current:
                result.append(''.join(current))
                current = []
                latin = False
        if current:
            result.append(''.join(current))
        return result

    tokens = tokenize(phrase)
    words = tokenize(quote)
    if not tokens:
        return False
    # CJK scripts commonly omit spaces between words; match the continuous
    # sequence, but retain whole-word boundaries for other writing systems.
    cjk = lambda word: any('\u3040' <= c <= '\u30ff' or '\u3400' <= c <= '\u9fff' for c in word)
    if any(cjk(token) for token in tokens):
        return ''.join(tokens) in ''.join(words)
    return any(words[i:i + len(tokens)] == tokens for i in range(len(words)))


def allowed(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == 'https' and parsed.hostname == 'clip.cafe'


def search_links(phrase: str, audio_language: str | None):
    """Prefer source language filters, then try unrestricted results.

    Source metadata is not proof of the MP4's spoken language; callers must
    verify audio before accepting multilingual clips.
    """
    base = {'s': f'"{phrase}"', 'usersearch': '1', 'ss': 's'}
    queries = ([dict(base, audio=audio_language, sl=audio_language), base]
               if audio_language else [base])
    seen = set()
    for query in queries:
        result = page(BASE + '?' + urlencode(query))
        for link in result.links[:15]:
            if link not in seen:
                seen.add(link)
                yield link


def find_clip(phrase: str, out_dir: Path = Path('clips'), *, verify=None, audio_language: str | None = None) -> Clip:
    for link in search_links(phrase, audio_language):
        url = urljoin(BASE, link)
        if not allowed(url):
            continue
        try:
            details = page(url)
            quote = details.meta.get('og:description', '')
            title = details.meta.get('og:title', '')
            video_url = details.meta.get('og:video:secure_url') or details.meta.get('og:video', '')
            if (verify is None and not matches(phrase, quote)) or not allowed(video_url):
                continue
            # Movie title appears after the separator in the page title.
            movie = title.rsplit('|', 1)[-1].strip().removesuffix(' scene').strip() or 'Film'
            slug = urlparse(video_url).path.rsplit('/', 1)[-1].removesuffix('.mp4')
            if not re.fullmatch(r'[A-Za-z0-9_-]+', slug):
                continue
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / f'clipcafe-{slug}.mp4'
            localized = False
            if audio_language and verify is not None:
                from hls_clips import download_localized
                localized = download_localized(slug, audio_language, path)
            if not localized:
                with get(video_url) as video:
                    if not allowed(video.url):
                        raise ValueError('Unexpected video redirect')
                    size = 0
                    try:
                        with path.open('wb') as output:
                            for chunk in iter(lambda: video.read(65536), b''):
                                size += len(chunk)
                                if size > MAX_BYTES:
                                    raise ValueError('Clip exceeds size limit')
                                output.write(chunk)
                        with path.open('rb') as f:
                            if size < 1024 or b'ftyp' not in f.read(64):
                                raise ValueError('Invalid MP4')
                    except Exception:
                        path.unlink(missing_ok=True)
                        raise
            if verify is not None:
                try:
                    verified = verify(path, phrase)
                except Exception:
                    path.unlink(missing_ok=True)
                    raise
                if not verified:
                    path.unlink(missing_ok=True)
                    log.info('Audio did not match the requested expression in clip %s', slug)
                    continue
            log.info('Selected Clip.Cafe clip %s: %s', slug, movie)
            return Clip(slug, movie, quote, url, path)
        except (URLError, ValueError, OSError) as exc:
            log.warning('Could not use clip %s: %s', url, exc)
    raise RuntimeError(f'No downloadable clip matching {phrase!r} found on Clip.Cafe')
