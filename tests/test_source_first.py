from types import SimpleNamespace
from unittest.mock import MagicMock
import source_first


def response(text):
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))])
    return client


def test_extraction_requires_actual_unseen_multiword_transcript(monkeypatch):
    monkeypatch.setattr(source_first.multilingual, 'client', lambda: response('{"text":"كيف حالك", "topic":"greeting"}'))
    assert source_first.extract_expression('مرحبا كيف حالك اليوم', 'ar', 'A2', set(), []) == ('كيف حالك', 'greeting')
    assert source_first.extract_expression('مرحبا صديقي', 'ar', 'A2', set(), []) is None
    assert source_first.extract_expression('مرحبا كيف حالك اليوم', 'ar', 'A2', {'كيف حالك'}, []) is None
    monkeypatch.setattr(source_first.multilingual, 'client', lambda: response('{"text":"مرحبا", "topic":"greeting"}'))
    assert source_first.extract_expression('مرحبا صديقي', 'ar', 'A2', set(), []) is None


def test_source_first_never_accepts_wrong_language_or_phrase(monkeypatch, tmp_path):
    import pytest
    monkeypatch.setattr(source_first, 'SEEDS', {'ja': ('こんにちは',)})
    monkeypatch.setattr(source_first.multilingual, 'transcript_for_language', lambda *args: 'さようなら')
    def search(seed, verify, audio_language):
        assert audio_language == 'ja'
        assert not verify(tmp_path / 'test.mp4', seed)
        raise RuntimeError('none')
    monkeypatch.setattr(source_first.clip_cafe, 'find_clip', search)
    with pytest.raises(RuntimeError):
        source_first.find_expression_clip('ja', 'A2', set(), [])
