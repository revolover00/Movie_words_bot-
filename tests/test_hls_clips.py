import json
import subprocess
from types import SimpleNamespace

import pytest
import hls_clips


def test_playlist_rejects_remote_and_encrypted_media():
    good = '#EXTM3U\n#EXT-X-MAP:URI="init.mp4"\n#EXTINF:2\nseg.m4s\n#EXT-X-ENDLIST\n'
    assert hls_clips.playlist_files(good) == {'init.mp4', 'seg.m4s'}
    for bad in [good.replace('seg.m4s', 'https://evil.test/a'),
                good.replace('seg.m4s', '../outside'),
                good.replace('#EXTINF', '#EXT-X-KEY:METHOD=AES-128\n#EXTINF'),
                good.replace('#EXT-X-ENDLIST', ''),
                good.replace('#EXTINF', '#EXT-X-PART:URI="/etc/passwd"\n#EXTINF'),
                good.replace('URI="init.mp4"', 'URI="../secret"')]:
        with pytest.raises(ValueError):
            hls_clips.playlist_files(bad)


def test_download_localized_uses_only_local_ffmpeg_inputs(monkeypatch, tmp_path):
    requests = []
    def read(url, limit):
        requests.append(url)
        if url.endswith('info.json'):
            return json.dumps({'hls_exists': True, 'imdb': 'tt12345', 'audio_languages': ['ja']}).encode()
        if url.endswith('.m3u8'):
            media = 'v.m4s' if 'video-' in url else 'a.m4s'
            return f'#EXTM3U\n#EXTINF:1\n{media}\n#EXT-X-ENDLIST\n'.encode()
        return b'part'
    monkeypatch.setattr(hls_clips, '_read', read)
    def ffmpeg(args, **kwargs):
        assert 'file' in args
        assert not any('https:' in part for part in args)
        (tmp_path / 'out.mp4').write_bytes(b'0000ftyp' + b'x' * 1100)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(hls_clips.subprocess, 'run', ffmpeg)
    assert hls_clips.download_localized('hello', 'ja', tmp_path / 'out.mp4')
    assert any('audio-ja.m3u8' in url for url in requests)


def test_missing_audio_track_never_builds_mp4(monkeypatch, tmp_path):
    monkeypatch.setattr(hls_clips, '_read', lambda *args: b'{"hls_exists":true,"imdb":"tt123","audio_languages":["en"]}')
    assert not hls_clips.download_localized('hello', 'hi', tmp_path / 'out.mp4')
    assert not (tmp_path / 'out.mp4').exists()
