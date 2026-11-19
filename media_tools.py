"""Locate the bundled FFmpeg binary without a system package manager."""
from __future__ import annotations

import shutil


def ffmpeg_executable() -> str:
    executable = shutil.which('ffmpeg')
    if executable:
        return executable
    from imageio_ffmpeg import get_ffmpeg_exe
    return get_ffmpeg_exe()
