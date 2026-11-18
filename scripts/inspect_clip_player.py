"""Inspect public HLS media playlists."""
from urllib.request import Request, urlopen
headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
def get(url):
    with urlopen(Request(url,headers=headers),timeout=30) as r: return r.read(100000).decode('utf-8','replace')
base='https://clip.cafe/hls/tt31425731/thanks-s750/'
parts=[]
for name in ('video-lq.m3u8','audio-ar.m3u8','audio-hi.m3u8'):
    try: parts.append(name+': '+get(base+name))
    except Exception as exc: parts.append(name+': '+type(exc).__name__)
print('::notice title=HLS media playlists::'+' | '.join(parts).replace('%','%25').replace('\n','%0A')[:60000],flush=True)
