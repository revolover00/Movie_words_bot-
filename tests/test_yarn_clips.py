from yarn_clips import _parse_title, CLIP_ID


def test_title_requires_whole_word_in_quote():
    page = '<title>YARN | Curious? | A Movie (2020) | Video clips by quotes | ID</title>'
    assert _parse_title(page, 'curious') == ('Curious?', 'A Movie (2020)')
    assert _parse_title(page, 'curio') is None
    assert _parse_title('<title>YARN | Hello | Curious Movie | Video clips</title>', 'curious') is None


def test_search_clip_ids_only():
    page = '<a href="/yarn-clip/305c386b-5828-4421-b5ee-372687117294">x</a>'
    assert CLIP_ID.findall(page) == ['305c386b-5828-4421-b5ee-372687117294']
