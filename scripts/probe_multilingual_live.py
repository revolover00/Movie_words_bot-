"""Live source, speech and generation probes; never sends bot messages."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clip_cafe import find_clip
from multilingual import verify_audio, expressions, meaning, NAMES

examples = {
    'en': 'Nice to meet you', 'es': 'muchas gracias', 'fr': 'je suis désolé',
    'ar': 'مرحبا', 'pt': 'muito obrigado', 'de': 'vielen dank',
    'ru': 'спасибо', 'hi': 'नमस्ते', 'ja': 'こんにちは', 'zh': '谢谢',
}
results = []
with TemporaryDirectory() as out:
    for lang, phrase in examples.items():
        try:
            options = expressions(lang, 'A2', set(), [])
            text = meaning(phrase, lang, 'ar', 'A2')
            results.append(f'{lang}:text=ok')
        except Exception as exc:
            results.append(f'{lang}:text={type(exc).__name__}')
        try:
            clip = find_clip(phrase, Path(out), verify=lambda path, text: verify_audio(path, text, lang))
            results.append(f'{lang}:audio=ok')
        except Exception as exc:
            results.append(f'{lang}:audio={type(exc).__name__}')

print('::notice title=Multilingual probe::' + '; '.join(results), flush=True)
