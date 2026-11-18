from clip_cafe import PageParser, allowed, matches


def test_quote_requires_the_complete_phrase():
    assert matches('Nice to meet you', 'Hello! Nice to meet you, sir.')
    assert not matches('Nice to meet you', 'Nice to see you.')
    assert matches('Take your time', 'Take your time!')


def test_parse_search_and_metadata():
    p = PageParser()
    p.feed('<picture data-link="movie/quote/"></picture><meta property="og:description" content="Nice &amp; easy"><meta property="og:video" content="https://clip.cafe/videos/a.mp4">')
    assert p.links == ['movie/quote/']
    assert p.meta['og:description'] == 'Nice & easy'
    assert allowed(p.meta['og:video'])
    assert not allowed('https://clip.cafe.evil.example/videos/a.mp4')
