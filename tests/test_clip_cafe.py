from clip_cafe import PageParser, allowed, matches


def test_quote_requires_the_complete_phrase():
    assert matches('Nice to meet you', 'Hello! Nice to meet you, sir.')
    assert not matches('Nice to meet you', 'Nice to see you.')
    assert matches('Take your time', 'Take your time!')


def test_multilingual_matching_and_non_latin_text():
    assert matches('Comment ça va', 'Bonjour ! Comment ça va ?')
    assert matches('¿Cómo estás?', 'Hola, como estas?')
    assert matches('كيف حالك', 'مرحبا، كيف حالك؟')
    assert matches('कैसे हो', 'नमस्ते, कैसे हो?')
    assert not matches('कैसे हो', 'नमस्ते, किस हो?')
    assert matches('你好', '你好朋友！')
    assert matches('ありがとうございます', '本当にありがとうございます。')
    assert not matches('привет', 'пока друг')
    assert not matches('你好', '再见朋友')


def test_parse_search_and_metadata():
    p = PageParser()
    p.feed('<picture data-link="movie/quote/"></picture><meta property="og:description" content="Nice &amp; easy"><meta property="og:video" content="https://clip.cafe/videos/a.mp4">')
    assert p.links == ['movie/quote/']
    assert p.meta['og:description'] == 'Nice & easy'
    assert allowed(p.meta['og:video'])
    assert not allowed('https://clip.cafe.evil.example/videos/a.mp4')


def test_result_audio_languages_are_indexed():
    parser = PageParser()
    parser.feed('<picture data-link="movie/a/"></picture><span aria-label="Audio: French, English"></span>')
    assert parser.audio_languages['movie/a/'] == {'french', 'english'}


def test_search_includes_audio_and_transcript_language(monkeypatch, tmp_path):
    import clip_cafe
    from urllib.parse import urlparse, parse_qs
    urls = []
    def search(url):
        urls.append(url)
        return PageParser()
    monkeypatch.setattr(clip_cafe, 'page', search)
    import pytest
    with pytest.raises(RuntimeError):
        clip_cafe.find_clip('こんにちは', tmp_path, audio_language='ja')
    assert parse_qs(urlparse(urls[0]).query)['audio'] == ['ja']
    assert parse_qs(urlparse(urls[0]).query)['sl'] == ['ja']


def test_search_falls_back_without_duplicate_clips(monkeypatch):
    import clip_cafe
    from urllib.parse import parse_qs, urlparse
    calls = []
    def search(url):
        calls.append(parse_qs(urlparse(url).query))
        p = PageParser()
        p.links = ['a', 'b'] if len(calls) == 1 else ['b', 'c']
        return p
    monkeypatch.setattr(clip_cafe, 'page', search)
    assert list(clip_cafe.search_links('hola', 'es')) == ['a', 'b', 'c']
    assert calls[0]['audio'] == ['es']
    assert 'audio' not in calls[1]


def test_search_language_can_differ_from_audio(monkeypatch):
    import clip_cafe
    from urllib.parse import parse_qs, urlparse
    urls = []
    def search(url):
        urls.append(url)
        return PageParser()
    monkeypatch.setattr(clip_cafe, 'page', search)
    list(clip_cafe.search_links('thank you', 'hi', 'en'))
    query = parse_qs(urlparse(urls[0]).query)
    assert query['audio'] == ['hi'] and query['sl'] == ['en']


def test_clip_search_stops_after_time_budget(monkeypatch, tmp_path):
    import clip_cafe
    import pytest
    ticks = iter([100, 146])
    monkeypatch.setattr(clip_cafe.time, 'monotonic', lambda: next(ticks))
    monkeypatch.setattr(clip_cafe, 'search_links', lambda *args: iter(['movie/a/']))
    monkeypatch.setattr(clip_cafe, 'page', lambda *args: pytest.fail('Should stop before downloading'))
    with pytest.raises(RuntimeError):
        clip_cafe.find_clip('hello', tmp_path, max_seconds=45)


def test_redirect_policy_rejects_untrusted_destinations():
    from urllib.request import Request
    from clip_cafe import SafeRedirect
    import pytest
    req = Request('https://clip.cafe/a')
    for url in ('https://evil.example/', 'http://127.0.0.1/', 'https://clip.cafe:444/a', 'https://u@clip.cafe/a'):
        assert not allowed(url)
        with pytest.raises(ValueError):
            SafeRedirect().redirect_request(req, None, 302, 'Found', {}, url)


def test_allowed_rejects_malformed_urls():
    assert not allowed('https://[bad-host/a')
    assert not allowed('https://clip.cafe:bad/a')


def test_bounded_search_samples_beyond_top_results(monkeypatch):
    import clip_cafe
    p = PageParser()
    p.links = [str(i) for i in range(20)]
    monkeypatch.setattr(clip_cafe, 'page', lambda url: p)
    monkeypatch.setattr(clip_cafe.random, 'sample', lambda population, k: population[-k:])
    assert list(clip_cafe.search_links('hi', None, limit=6)) == ['0', '1', '2', '17', '18', '19']
