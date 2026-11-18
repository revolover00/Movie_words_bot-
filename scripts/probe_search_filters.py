import sys, re
from pathlib import Path
from urllib.parse import urlencode, urljoin
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clip_cafe import page, get, BASE
lang='ru'; phrase='спасибо'
r = page(BASE + '?' + urlencode({'s': f'"{phrase}"', 'usersearch': '1', 'ss': 's', 'audio': lang, 'sl': lang}))
url=urljoin(BASE, r.links[0])
with get(url) as resp: html=resp.read(2000000).decode('utf-8','replace')
parts = []
for pattern in [r'.{0,120}\.mp4.{0,200}', r'.{0,100}audio.{0,180}', r'.{0,100}language.{0,180}']:
    parts.extend(re.findall(pattern, html, flags=re.I)[:8])
print('::notice title=Clip source metadata::' + ' | '.join(parts).replace('%','%25').replace('\n',' '), flush=True)
