"""Inspect bounded discovery ordering without delivering messages."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import clip_cafe
for text, sl in [('thank you', 'en'), ('नमस्ते', 'hi')]:
    try:
        links=list(clip_cafe.search_links(text,'hi',sl,15))
        print(f'::notice title=Hindi search {sl}::'+', '.join(links[:20]), flush=True)
    except Exception as exc:
        print(f'::warning title=Hindi search {sl}::{type(exc).__name__}', flush=True)
