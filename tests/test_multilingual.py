from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import multilingual


def test_generated_expressions_are_checked(monkeypatch):
    fake = MagicMock()
    fake.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"expressions":[{"text":"Hola amigo", "topic":"greetings"},{"text":"seen", "topic":"work"}]}'))])
    monkeypatch.setattr(multilingual, 'client', lambda: fake)
    assert multilingual.expressions('es', 'A2', {'seen'}, []) == [('Hola amigo', 'greetings')]
    with pytest.raises(ValueError):
        multilingual.expressions('xx', 'A2', set(), [])


def test_audio_verification_rejects_wrong_language_or_phrase(monkeypatch, tmp_path):
    clip = tmp_path / 'sample.mp4'
    clip.write_bytes(b'fake video')
    fake = MagicMock()
    monkeypatch.setattr(multilingual, 'client', lambda: fake)
    fake.audio.transcriptions.create.return_value = SimpleNamespace(language='english', text='Nice to meet you.')
    assert multilingual.verify_audio(clip, 'Nice to meet you', 'en')
    assert not multilingual.verify_audio(clip, 'Nice to meet you', 'es')
    assert not multilingual.verify_audio(clip, 'Good morning', 'en')


def test_stream_hint_avoids_transcribing_wrong_language(monkeypatch, tmp_path):
    clip = tmp_path / 'sample.mp4'
    clip.write_bytes(b'fake')
    fake = MagicMock()
    monkeypatch.setattr(multilingual, 'client', lambda: fake)
    monkeypatch.setattr(multilingual.subprocess, 'run', lambda *a, **kw: SimpleNamespace(stdout='{"streams":[{"tags":{"language":"eng"}}]}'))
    assert not multilingual.verify_audio(clip, 'こんにちは', 'ja')
    fake.audio.transcriptions.create.assert_not_called()
    assert multilingual.likely_audio_language(clip, 'en')


def test_unknown_stream_language_falls_back_to_transcription(monkeypatch, tmp_path):
    monkeypatch.setattr(multilingual.subprocess, 'run', lambda *a, **kw: SimpleNamespace(stdout='{"streams":[{"tags":{"language":"und"}}]}'))
    assert multilingual.likely_audio_language(tmp_path / 'clip.mp4', 'ja')


def test_single_word_expression_is_rejected_for_space_delimited_language(monkeypatch):
    fake = MagicMock()
    fake.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"expressions":[{"text":"Hola", "topic":"greeting"},{"text":"Muchas gracias", "topic":"thanks"}]}'))])
    monkeypatch.setattr(multilingual, 'client', lambda: fake)
    assert multilingual.expressions('es', 'A2', set(), []) == [('Muchas gracias', 'thanks')]
