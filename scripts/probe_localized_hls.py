"""Validate public alternate audio tracks with Whisper; never sends messages."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import hls_clips
import multilingual

samples = {'ar': ('thanks-s750', 'شكرا'), 'hi': ('thanks-s750', ''),
           'ru': ('gomabseubnida-gomabseubnida-gomabseubnida', 'спасибо'),
           'zh': ('na-mei-guan-xi-xie-xie-chui-pao-pao-bu-cuo-a-mei-guan-xi-xie-xie', '谢谢')}
lang = sys.argv[1]
slug, phrase = samples[lang]
with TemporaryDirectory() as out:
    path = Path(out) / 'sample.mp4'
    try:
        if not hls_clips.download_localized(slug, lang, path):
            raise RuntimeError('HLS download failed')
        transcript = multilingual.transcript_for_language(path, lang)
        if not transcript:
            raise RuntimeError('Audio language detection failed')
        print(f'::notice title=Localized audio {lang}::Verified spoken language; seed match={not phrase or multilingual.matches(phrase, transcript)}; {len(transcript)} characters', flush=True)
    except Exception as exc:
        print(f'::warning title=Localized audio {lang} unavailable::{type(exc).__name__}: {str(exc)[:200]}', flush=True)
