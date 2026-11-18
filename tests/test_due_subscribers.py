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
    assert '<= now()' in sql


def test_advance_new_subscriber_does_not_overwrite_concurrent_settings(monkeypatch):
    cur = mock_db(monkeypatch, row=None)
    assert not db.advance_due_after_delivery(42, None)
    sql, params = cur.execute.call_args.args
    assert 'ON CONFLICT (chat_id) DO NOTHING' in sql
    assert params == (42,)


def test_advance_existing_subscriber_checks_version(monkeypatch):
    cur = mock_db(monkeypatch, row=(42,))
    assert db.advance_due_after_delivery(42, 'version')
    sql, params = cur.execute.call_args.args
    assert 'p.updated_at = %s' in sql
    assert params == (42, 'version')
