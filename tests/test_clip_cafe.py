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
