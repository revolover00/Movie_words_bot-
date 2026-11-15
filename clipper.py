"""Download a short clip around a word using yt-dlp + FFmpeg.

Pipeline:
    1. Fetch auto subtitles (SRT) for the video.
    2. Find the first cue containing the word.
    3. Download only [start - before, end + after] via yt-dlp sections.
    4. Re-encode with FFmpeg (H.264/AAC, max 1280px) for Telegram.
"""

from __future__ import annotations

import logging
import re
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

_SRT_TIME = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)")


def _srt_to_seconds(ts: str) -> float:
    m = _SRT_TIME.search(ts)
    if not m:
        return 0.0
    h, mnt, s, ms = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + int(s) + int(ms) / 1000.0


def parse_srt(path: Path) -> list[tuple[float, float, str]]:
    """Parse an SRT file into (start, end, text) cues."""
    cues: list[tuple[float, float, str]] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        start_s, end_s = lines[1].split("-->")
        body = " ".join(lines[2:])
        cues.append((_srt_to_seconds(start_s), _srt_to_seconds(end_s), body))
    return cues


def find_word_time(cues: list[tuple[float, float, str]], word: str) -> tuple[float, float] | None:
    """Return (start, end) of the first cue containing `word`."""
    pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
    for start, end, text in cues:
        if pattern.search(text):
            return start, end
    return None


def _run(cmd: list[str]) -> None:
    log.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def fetch_subtitles(video_id: str, tmp: Path) -> list[tuple[float, float, str]]:
    """Download auto subtitles and parse them."""
    _run(
        [
            "yt-dlp",
            "--write-auto-subs",
            "--sub-format", "srt",
            "--sub-langs", "en.*",
            "--skip-download",
            "-o", str(tmp / "subs.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}",
        ]
    )
    srt_files = sorted(tmp.glob("subs*.srt"))
    if not srt_files:
        return []
    return parse_srt(srt_files[0])


def download_clip(
    video_id: str,
    start: float,
    end: float,
    out_path: Path,
) -> Path:
    """Download [start, end] of the video and re-encode for Telegram."""
    section = f"*{start:.2f}-{end:.2f}"
    raw = out_path.with_suffix(".raw.mp4")
    _run(
        [
            "yt-dlp",
            "--download-sections", section,
            "-f", "bv*[height<=720]+ba/b[height<=720]/b",
            "--force-keyframes-at-cuts",
            "-o", str(raw),
            f"https://www.youtube.com/watch?v={video_id}",
        ]
    )
    _run(
        [
            "ffmpeg", "-y",
            "-i", str(raw),
            "-vf", "scale=1280:-2",
            "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(out_path),
        ]
    )
    raw.unlink(missing_ok=True)
    return out_path


def get_clip(video_id: str, word: str, before: int = 2, after: int = 3) -> Path:
    """Full pipeline: subtitles -> timestamp -> clip file.

    Falls back to a 10-second clip from 0:30 if the word is not found.
    """
    with tempfile.TemporaryDirectory(prefix="movie-word-") as td:
        tmp = Path(td)
        start, end = 30.0, 40.0
        try:
            cues = fetch_subtitles(video_id, tmp)
            hit = find_word_time(cues, word)
            if hit:
                start = max(0.0, hit[0] - before)
                end = hit[1] + after
                log.info("Word %r found at %.1fs-%.1fs", word, hit[0], hit[1])
            else:
                log.warning("Word %r not in subtitles, using fallback window", word)
        except subprocess.CalledProcessError as exc:
            log.warning("Subtitle fetch failed (%s), using fallback window", exc)

        out = Path("clips") / f"{video_id}_{int(start)}s.mp4"
        out.parent.mkdir(exist_ok=True)
        return download_clip(video_id, start, end, out)
