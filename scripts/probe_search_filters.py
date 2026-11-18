import json, re, subprocess, sys, tempfile
from pathlib import Path
from urllib.parse import urlencode, urljoin
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clip_cafe import page, get, BASE
examples={'ru':'спасибо','ja':'こんにちは','ar':'مرحبا','zh':'谢谢','de':'vielen dank'}
result=[]
with tempfile.TemporaryDirectory() as tmp:
    for lang, phrase in examples.items():
        try:
            r=page(BASE+'?'+urlencode({'s': f'"{phrase}"','usersearch':'1','ss':'s','audio':lang,'sl':lang}))
            d=page(urljoin(BASE,r.links[0])); u=d.meta['og:video']
            path=Path(tmp)/f'{lang}.mp4'
            with get(u) as v: path.write_bytes(v.read(20*1024*1024))
            p=subprocess.run(['ffprobe','-v','error','-show_entries','stream=index,codec_type:stream_tags=language,title','-of','json',str(path)],capture_output=True,text=True,timeout=30,check=True)
            result.append(f'{lang}: '+json.dumps(json.loads(p.stdout)['streams'],ensure_ascii=False,separators=(',',':')))
        except Exception as exc: result.append(f'{lang}: {type(exc).__name__}')
print('::notice title=Audio streams::'+'; '.join(result),flush=True)
