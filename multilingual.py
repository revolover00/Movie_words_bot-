"""Generate learner-level expressions and verify the language of clip audio."""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from openai import OpenAI

from clip_cafe import matches
from config import config
from preferences import LANGUAGES, validate_language

log = logging.getLogger(__name__)
NAMES = {item['code']: item['name'] for item in LANGUAGES}
DETECTED_NAMES = {
    'en': {'english', 'en'}, 'zh': {'chinese', 'mandarin', 'zh'},
    'hi': {'hindi', 'hi'}, 'es': {'spanish', 'es'}, 'fr': {'french', 'fr'},
    'ar': {'arabic', 'ar'}, 'pt': {'portuguese', 'pt'}, 'ru': {'russian', 'ru'},
    'de': {'german', 'de'}, 'ja': {'japanese', 'ja'},
}


def client() -> OpenAI:
    config.validate('groq_api_key')
    return OpenAI(base_url='https://api.groq.com/openai/v1', api_key=config.groq_api_key, timeout=30, max_retries=1)


def expressions(language: str, level: str, seen: set[str], recent_topics: list[str]) -> list[tuple[str, str]]:
    """Ask for short, diverse original-script phrases, avoiding prior expressions."""
    validate_language(language)
    prompt = (f'Create 12 short, natural, useful spoken {NAMES[language]} expressions for '
              f'CEFR {level}. Use the original writing system, not romanization. '
              'Cover different everyday topics. Avoid proper names and single words. '
              f'Avoid these recent topics: {", ".join(recent_topics[:3])}. '
              f'Avoid these already-used phrases: {", ".join(list(seen)[-100:])}. '
              'Return only JSON: {"expressions": [{"text": "...", "topic": "..."}]}')
    response = client().chat.completions.create(
        model=config.groq_model, messages=[{'role': 'user', 'content': prompt}],
        temperature=0.6, max_tokens=1200, response_format={'type': 'json_object'},
    )
    raw = json.loads(response.choices[0].message.content or '{}')
    items = raw.get('expressions', []) if isinstance(raw, dict) else []
    if not isinstance(items, list):
        raise ValueError('Model did not return a list of expressions')
    result = []
    for item in items[:20]:
        if not isinstance(item, dict):
            continue
        text, topic = item.get('text'), item.get('topic')
        if not isinstance(text, str) or not isinstance(topic, str):
            continue
        text, topic = text.strip(), topic.strip()
        # Chinese and Japanese do not reliably separate words with spaces.
        multiword = language in {'zh', 'ja'} or len(text.split()) >= 2
        if (multiword and 2 <= len(text) <= 100 and 1 <= len(topic) <= 50
                and '\n' not in text and text.casefold() not in seen):
            result.append((text, topic))
    if not result:
        raise ValueError('Model returned no valid new expressions')
    return result


def meaning(phrase: str, learning: str, explanation: str, level: str) -> str:
    validate_language(learning)
    validate_language(explanation)
    language = 'Egyptian Arabic' if explanation == 'ar' else NAMES[explanation]
    prompt = (f'Teach this {NAMES[learning]} expression to a {level} learner: {phrase!r}. '
              f'Write a concise explanation in {language}, then one short example '
              f'in {NAMES[learning]} and its translation into {language}. '
              'Do not change the expression or add unrelated content.')
    response = client().chat.completions.create(
        model=config.groq_model, messages=[{'role': 'user', 'content': prompt}],
        temperature=0.3, max_tokens=350,
    )
    result = (response.choices[0].message.content or '').strip()
    if not result:
        raise ValueError('Model returned an empty explanation')
    return result



# MP4 stream tags are only a fast rejection hint: unknown tags still go to
# Whisper, and every accepted clip must pass transcription verification.
STREAM_LANGUAGES = {
    'en': {'eng'}, 'zh': {'zho', 'chi'}, 'hi': {'hin'}, 'es': {'spa'},
    'fr': {'fra', 'fre'}, 'ar': {'ara'}, 'pt': {'por'}, 'ru': {'rus'},
    'de': {'deu', 'ger'}, 'ja': {'jpn'},
}


def likely_audio_language(path: Path, language: str) -> bool:
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries',
             'stream_tags=language', '-of', 'json', str(path)],
            capture_output=True, text=True, timeout=10, check=True,
        )
        streams = json.loads(result.stdout).get('streams', [])
        tag = (streams[0].get('tags', {}).get('language', '') if streams else '').lower()
        return not tag or tag == 'und' or tag in STREAM_LANGUAGES[language]
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, AttributeError):
        return True


def verify_audio(path: Path, expression: str, language: str) -> bool:
    """Fail closed unless speech-to-text identifies the language and phrase.

    Automatic transcription is imperfect; it is a best-effort check, not a
    guarantee. A failure to access the API is not treated as a verified clip.
    """
    validate_language(language)
    if not likely_audio_language(path, language):
        return False
    with path.open('rb') as video:
        transcript = client().audio.transcriptions.create(
            model='whisper-large-v3-turbo', file=video,
            response_format='verbose_json', temperature=0,
        )
    detected = (getattr(transcript, 'language', '') or '').casefold()
    text = getattr(transcript, 'text', '') or ''
    return detected in DETECTED_NAMES[language] and matches(expression, text)
