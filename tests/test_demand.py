import asyncio
from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock
import daily_job


def sub(chat, learning='en', explanation='ar'):
    return dict(chat_id=chat, level='B1', learning_language=learning,
                explanation_language=explanation, settings_updated_at=None)


def test_empty_audience_does_not_construct_bot_or_generate(monkeypatch):
    bot = Mock(side_effect=AssertionError('no bot needed'))
    generate = Mock(side_effect=AssertionError('no content needed'))
    monkeypatch.setattr(daily_job, 'Bot', bot)
    monkeypatch.setattr(daily_job, 'select_localized_clip', generate)
    asyncio.run(daily_job.run_due_subscribers([]))
    bot.assert_not_called()
    generate.assert_not_called()


def test_no_longer_due_does_not_generate(monkeypatch):
    monkeypatch.setattr(daily_job.db, 'still_due_with_settings', lambda _: False)
    generate = Mock()
    monkeypatch.setattr(daily_job, 'select_localized_clip', generate)
    asyncio.run(daily_job.run_due_subscribers([sub(1)]))
    generate.assert_not_called()


def test_identical_content_shared_across_intervals_and_only_requested_languages(monkeypatch):
    monkeypatch.setattr(daily_job, 'Bot', lambda **_: object())
    monkeypatch.setattr(daily_job.db, 'still_due_with_settings', lambda _: True)
    monkeypatch.setattr(daily_job.db, 'advance_due_after_delivery', lambda *_: True)
    monkeypatch.setattr(daily_job.db, 'mark_phrase_sent', lambda *_: None)
    generate = Mock(return_value=(SimpleNamespace(text='Example', topic='test'), SimpleNamespace(path='unused', clip_id='1', title='Movie')))
    caption = Mock(return_value='Explanation')
    send = AsyncMock(return_value=(1, 0))
    monkeypatch.setattr(daily_job, 'select_localized_clip', generate)
    monkeypatch.setattr(daily_job, 'localized_caption', caption)
    monkeypatch.setattr(daily_job, 'broadcast', send)
    audience = [dict(sub(1), interval_minutes=30), dict(sub(2), interval_minutes=1440), sub(3, explanation='es')]
    asyncio.run(daily_job.run_due_subscribers(audience))
    generate.assert_called_once_with('B1', 'en')
    assert caption.call_count == 2
    assert {call.args[-1] for call in caption.call_args_list} == {'ar', 'es'}
    assert send.call_count == 3


def test_settings_change_after_content_search_skips_explanation(monkeypatch):
    checks = iter([True, True, False])
    monkeypatch.setattr(daily_job.db, 'still_due_with_settings', lambda _: next(checks))
    monkeypatch.setattr(daily_job, 'Bot', lambda **_: object())
    monkeypatch.setattr(daily_job, 'select_localized_clip', Mock(return_value=(object(), object())))
    caption = Mock()
    monkeypatch.setattr(daily_job, 'localized_caption', caption)
    asyncio.run(daily_job.run_due_subscribers([sub(1)]))
    caption.assert_not_called()


def test_idle_scheduler_does_not_require_ai_credentials(monkeypatch):
    validated = []
    monkeypatch.setattr(daily_job, 'config', SimpleNamespace(validate=lambda *names: validated.append(names)))
    monkeypatch.setattr(daily_job.db, 'init_db', lambda: None)
    monkeypatch.setattr(daily_job.db, 'due_subscribers', lambda: [])
    record = Mock()
    monkeypatch.setattr(daily_job.db, 'record_delivery_run', record)
    run = Mock()
    monkeypatch.setattr(daily_job.asyncio, 'run', run)
    daily_job.main()
    assert validated == [('database_url', 'bot_token')]
    run.assert_not_called()
    record.assert_called_once_with('idle', 0)
