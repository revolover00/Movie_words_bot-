from unittest.mock import MagicMock

import db


def mock_db(monkeypatch, *, rows=None, row=None):
    conn = MagicMock()
    cur = MagicMock()
    conn.__enter__.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cur
    cur.fetchall.return_value = rows or []
    cur.fetchone.return_value = row
    monkeypatch.setattr(db, 'connect', lambda: conn)
    return cur


def test_due_query_excludes_inactive_and_uses_database_time(monkeypatch):
    cur = mock_db(monkeypatch, rows=[{'chat_id': 1, 'level': 'A2'}])
    assert db.due_subscribers() == [{'chat_id': 1, 'level': 'A2'}]
    sql = cur.execute.call_args.args[0]
    assert 's.is_active = TRUE' in sql
    assert "COALESCE(p.input_state, '') NOT LIKE 'setup_%'" in sql
    assert '<= now()' in sql


def test_advance_new_subscriber_does_not_overwrite_concurrent_settings(monkeypatch):
    cur = mock_db(monkeypatch, row=None)
    assert not db.advance_due_after_delivery(42, None)
    sql, params = cur.execute.call_args_list[0].args
    assert 'ON CONFLICT (chat_id) DO NOTHING' in sql
    assert params == (42,)
    fallback, params = cur.execute.call_args_list[1].args
    assert '<= now()' in fallback and params == (42,)


def test_advance_existing_subscriber_checks_version(monkeypatch):
    cur = mock_db(monkeypatch, row=(42,))
    assert db.advance_due_after_delivery(42, 'version')
    sql, params = cur.execute.call_args.args
    assert 'p.updated_at = %s' in sql
    assert params == (42, 'version')


def test_preflight_checks_current_level_preferences_and_due_time(monkeypatch):
    cur = mock_db(monkeypatch, row=(1,))
    user = dict(chat_id=1, level='B1', learning_language='ja', explanation_language='ar', settings_updated_at='v')
    assert db.still_due_with_settings(user)
    sql, params = cur.execute.call_args.args
    assert 's.is_active = TRUE' in sql and 's.level = %s' in sql
    assert "LEFT(COALESCE(p.input_state, ''), 6) <> 'setup_'" in sql
    assert 'IS NOT DISTINCT FROM' in sql and '<= now()' in sql
    assert params == (1, 'B1', 'ja', 'ar', 'v', 0)


def test_advance_changed_settings_only_when_current_schedule_is_overdue(monkeypatch):
    cur = mock_db(monkeypatch)
    cur.fetchone.side_effect = [None, (42,)]
    assert db.advance_due_after_delivery(42, 'old-version')
    first, fallback = [call.args[0] for call in cur.execute.call_args_list]
    assert 'p.updated_at = %s' in first
    assert "next_delivery_at(p.interval_minutes)" in fallback
    assert "<= now()" in fallback


def test_lookahead_is_parameterized_and_preflight_uses_same_horizon(monkeypatch):
    cur = mock_db(monkeypatch, row=(1,))
    db.due_subscribers(10)
    assert cur.execute.call_args.args[1] == (10,)
    user = dict(chat_id=1, level='B1', learning_language='ja', explanation_language='ar', settings_updated_at='v')
    assert db.still_due_with_settings(user, 10)
    assert cur.execute.call_args.args[1][-1] == 10
