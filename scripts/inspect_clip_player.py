"""Inspect public HLS metadata and master manifests."""
import json
from urllib.request import Request, urlopen
headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
def get(url):
    with urlopen(Request(url,headers=headers),timeout=30) as r: return r.read(100000).decode('utf-8','replace')
parts=[]
for slug in ('gomabseubnida-gomabseubnida-gomabseubnida','na-mei-guan-xi-xie-xie-chui-pao-pao-bu-cuo-a-mei-guan-xi-xie-xie','thanks-s750'):
    try:
        info=json.loads(get(f'https://clip.cafe/hls/{slug}/info.json'))
        parts.append(f'{slug}: {json.dumps(info)}')
        if info.get('imdb') and info.get('hls_exists'):
            parts.append('MASTER: '+get(f'https://clip.cafe/hls/{info["imdb"]}/{slug}/master.m3u8'))
    except Exception as exc: parts.append(f'{slug}: {type(exc).__name__}')
print('::notice title=HLS manifests::'+' | '.join(parts).replace('%','%25').replace('\n','%0A')[:60000],flush=True)
