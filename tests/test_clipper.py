"""Tests for clipper subtitle parsing."""

from pathlib import Path

from clipper import find_word_time, parse_srt

SRT = """1
00:00:01,000 --> 00:00:03,000
Hello there, brave one.

2
00:00:05,500 --> 00:00:07,000
We must escape now!
"""


def test_parse_srt(tmp_path: Path):
    p = tmp_path / "subs.srt"
    p.write_text(SRT, encoding="utf-8")
    cues = parse_srt(p)
    assert len(cues) == 2
    assert cues[0][0] == 1.0
    assert cues[0][1] == 3.0
    assert "brave" in cues[0][2]


def test_find_word_time(tmp_path: Path):
    p = tmp_path / "subs.srt"
    p.write_text(SRT, encoding="utf-8")
    cues = parse_srt(p)
    hit = find_word_time(cues, "escape")
    assert hit is not None
    assert hit[0] == 5.5
    assert hit[1] == 7.0


def test_find_word_time_case_insensitive(tmp_path: Path):
    p = tmp_path / "subs.srt"
    p.write_text(SRT, encoding="utf-8")
    cues = parse_srt(p)
    assert find_word_time(cues, "BRAVE") is not None


def test_find_word_time_missing(tmp_path: Path):
    p = tmp_path / "subs.srt"
    p.write_text(SRT, encoding="utf-8")
    cues = parse_srt(p)
    assert find_word_time(cues, "nonexistent") is None
