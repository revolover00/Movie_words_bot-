"""Tests for words loading."""

from words import load_words


def test_load_words(tmp_path):
    p = tmp_path / "words.txt"
    p.write_text("# comment\nbrave\n\ncurious\n", encoding="utf-8")
    assert load_words(str(p)) == ["brave", "curious"]


def test_load_words_missing(tmp_path):
    try:
        load_words(str(tmp_path / "nope.txt"))
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")
