"""Inspect public result metadata to distinguish subtitles from audio."""
from urllib.parse import urlencode
from clip_cafe import BASE, get

for phrase in ('спасибо', 'こんにちは', 'مرحبا'):
    url = BASE + '?' + urlencode({'s': phrase, 'usersearch': '1', 'ss': 's'})
    with get(url) as response:
        html = response.read().decode('utf-8', 'replace')
    i = html.find('class="searchResultClip"')
    sample = html[i:i+6000] if i >= 0 else 'not found'
    sample = sample.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    print(f'::notice title=Search {phrase}::{sample[:6000]}')
