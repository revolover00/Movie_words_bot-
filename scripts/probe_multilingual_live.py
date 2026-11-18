"""Live opt-in source/audio check; never sends messages or changes user data."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clip_cafe import find_clip
from multilingual import verify_audio, NAMES

examples = {
    'en': 'Nice to meet you', 'es': 'muchas gracias', 'fr': 'je suis désolé',
    'ar': 'مرحبا', 'pt': 'muito obrigado', 'de': 'vielen dank',
    'ru': 'спасибо', 'hi': 'नमस्ते', 'ja': 'こんにちは', 'zh': '谢谢',
}
with TemporaryDirectory() as out:
    for lang, phrase in examples.items():
        try:
            clip = find_clip(phrase, Path(out), verify=lambda path, text: verify_audio(path, text, lang), audio_language=NAMES[lang].replace("Mandarin Chinese", "Chinese"))
            print(f'::notice title=Audio {lang}::Verified clip {clip.clip_id}', flush=True)
        except Exception as exc:
            print(f'::warning title=Audio {lang} unavailable::{type(exc).__name__}', flush=True)
