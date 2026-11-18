import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import daily_job
import phrases


def test_levels_have_multiple_topics_and_full_expressions():
    assert set(phrases.BANK) == set(phrases.LEVELS)
    for entries in phrases.BANK.values():
        assert len(entries) >= 20
        assert len({p.topic for p in entries}) >= 5
        assert all(len(p.text.split()) >= 2 for p in entries)


def test_candidates_exclude_seen_and_prefer_new_topics():
    entries = phrases.BANK['A2']
    seen = {entries[0].text.casefold()}
    result = phrases.candidates('A2', seen, ['greetings'])
    assert all(p.text.casefold() not in seen for p in result)
    assert result[0].topic != 'greetings'


def test_groups_receive_their_own_expression(monkeypatch):
    builds = []
    marked = []
    async def send(bot, chat_ids, path, caption):
        builds.append((chat_ids, caption))
        return len(chat_ids), 0
    monkeypatch.setattr(daily_job, 'Bot', lambda **kwargs: object())
    monkeypatch.setattr(daily_job, 'build_message', lambda level: (
        phrases.BANK[level][0], SimpleNamespace(path='/clip', clip_id=level, title='Movie'), level))
    monkeypatch.setattr(daily_job, 'broadcast', send)
    monkeypatch.setattr(daily_job.db, 'mark_phrase_sent', lambda *args: marked.append(args))
    asyncio.run(daily_job.run_groups({'A2': [1, 2], 'C1': [3]}))
    assert builds == [([1, 2], 'A2'), ([3], 'C1')]
    assert [x[0] for x in marked] == ['A2', 'C1']


def test_failed_delivery_does_not_mark_expression(monkeypatch):
    import pytest
    marked = []
    monkeypatch.setattr(daily_job, 'Bot', lambda **kwargs: object())
    monkeypatch.setattr(daily_job, 'build_message', lambda level: (
        phrases.BANK[level][0], SimpleNamespace(path='/clip', clip_id=level, title='Movie'), 'caption'))
    monkeypatch.setattr(daily_job, 'broadcast', AsyncMock(return_value=(0, 1)))
    monkeypatch.setattr(daily_job.db, 'mark_phrase_sent', lambda *args: marked.append(args))
    with pytest.raises(RuntimeError, match='A2'):
        asyncio.run(daily_job.run_groups({'A2': [1]}))
    assert not marked
