"""Tests for youtube_free helpers."""

from youtube_free import _parse_duration, _text


def test_parse_duration():
    assert _parse_duration("10:15") == 615
    assert _parse_duration("1:02:03") == 3723
    assert _parse_duration("") == 0
    assert _parse_duration("LIVE") == 0


def test_text_simple():
    assert _text({"simpleText": "Hello"}) == "Hello"


def test_text_runs():
    node = {"runs": [{"text": "Hello "}, {"text": "World"}]}
    assert _text(node) == "Hello World"


def test_text_empty():
    assert _text(None) == ""
    assert _text({}) == ""
