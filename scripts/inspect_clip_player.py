"""Inspect public player metadata; no download or Telegram delivery."""
import re
from urllib.request import Request, urlopen
url='https://clip.cafe/incantation-2022/na-mei-guan-xi-xie-xie-chui-pao-pao-bu-cuo-a-mei-guan-xi-xie-xie/'
headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
with urlopen(Request(url, headers=headers), timeout=30) as f: html=f.read(2000000).decode('utf-8','replace')
parts=[]
for pattern in [r'<script[^>]+src=["\'][^"\']+["\'][^>]*>', r'.{0,100}m3u8.{0,180}', r'.{0,100}audioTracks.{0,180}',r'.{0,100}audio_tracks.{0,180}',r'.{0,100}hls.{0,180}',r'.{0,100}data-audio.{0,180}']:
    parts.extend(re.findall(pattern,html,re.I)[:12])
print('::notice title=Player metadata::'+' | '.join(parts).replace('%','%25').replace('\n',' '),flush=True)
