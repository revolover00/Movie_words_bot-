"""Inspect search result counts and language metadata; no delivery."""
import sys
from pathlib import Path
from urllib.parse import urlencode
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clip_cafe import page, BASE
examples = {'ar': 'مرحبا', 'ru': 'спасибо', 'hi': 'नमस्ते', 'ja': 'こんにちは', 'zh': '谢谢', 'de': 'vielen dank'}
results = []
for lang, phrase in examples.items():
    try:
        q = urlencode({'s': f'"{phrase}"', 'usersearch': '1', 'ss': 's', 'audio': lang, 'sl': lang})
        r = page(BASE + '?' + q)
        results.append(f'{lang}: {len(r.links)} results, metadata={list(r.audio_languages.values())[:2]}')
    except Exception as exc:
        results.append(f'{lang}: {type(exc).__name__}')
print('::notice title=Filtered search::' + '; '.join(results), flush=True)
