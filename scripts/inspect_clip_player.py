"""Inspect public HLS URL and metadata construction."""
import re
from urllib.request import Request, urlopen
headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
def get(url):
    with urlopen(Request(url,headers=headers),timeout=30) as r: return r.read(2500000).decode('utf-8','replace')
parts=[]
for name,text,pats in [
 ('js',get('https://clip.cafe/js/main_min.js'),[r'function buildHlsUrl',r'buildHlsUrl\s*=',r'hlsInfo',r'master\.m3u8',r'https://[^"\' ]+hls[^"\' ]*']),
 ('html',get('https://clip.cafe/incantation-2022/na-mei-guan-xi-xie-xie-chui-pao-pao-bu-cuo-a-mei-guan-xi-xie-xie/'),[r'\.m3u8',r'hlsInfo',r'hls_info',r'\.m3u8',r'data-hls',r'imdb.{0,20}:'])]:
    for pat in pats:
        for m in list(re.finditer(pat,text,re.I))[:4]: parts.append(name+':'+text[max(0,m.start()-100):m.end()+450])
print('::notice title=HLS implementation::'+' | '.join(parts).replace('%','%25').replace('\n',' ')[:60000],flush=True)
