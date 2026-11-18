"""Integration-test the production clip lookup without sending Telegram messages."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clip_cafe import find_clip, matches

examples = {
    'A2': 'Nice to meet you',
    'B1': 'That makes sense',
    'B2': 'I owe you one',
    'C1': 'It is a long shot',
    'C2': 'The ball is in your court',
}
failed = []
with TemporaryDirectory() as directory:
    for level, expression in examples.items():
        try:
            clip = find_clip(expression, Path(directory))
            assert matches(expression, clip.quote)
            print(f'::notice title={level} clip::{expression}; {clip.title}; {clip.path.stat().st_size} bytes')
        except Exception as exc:
            failed.append(level)
            print(f'::error title={level} clip failed::{type(exc).__name__}: {exc}')
if failed:
    raise SystemExit('Clip tests failed: ' + ', '.join(failed))
