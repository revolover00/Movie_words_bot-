"""Inspect public player implementation without delivering messages."""
import re
from urllib.request import Request, urlopen
headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
parts=[]
for path in ('js/player-ui.js','js/main_min.js'):
    with urlopen(Request('https://clip.cafe/'+path, headers=headers), timeout=30) as f: text=f.read(2500000).decode('utf-8','replace')
    for pat in (r'm3u8',r'audioTracks',r'\.m3u8',r'hlsUrl',r'hls_url',r'audioTrack'):
        for m in list(re.finditer(pat,text,re.I))[:5]:
            parts.append(path+':'+text[max(0,m.start()-150):m.end()+200])
print('::notice title=Player implementation::'+' | '.join(parts).replace('%','%25').replace('\n',' ')[:60000],flush=True)
