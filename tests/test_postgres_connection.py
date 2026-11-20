from unittest.mock import MagicMock

import postgres_connection as transport


def test_python_database_tls_cannot_be_disabled_by_url(monkeypatch):
    connect = MagicMock()
    monkeypatch.setattr(transport.psycopg2, 'connect', connect)
    dsn = 'postgresql://user:password@example.com/db?sslmode=disable'
    assert transport.connect_verified(dsn) is connect.return_value
    args, options = connect.call_args
    assert args == (dsn,)
    assert options['sslmode'] == 'verify-full'
    assert options['sslrootcert'] == transport.certifi.where()
    assert options['connect_timeout'] == 10
    assert 'options' not in options
    connect.return_value.cursor.return_value.__enter__.return_value.execute.assert_called_once_with('SET statement_timeout = 15000')
    connect.return_value.commit.assert_called_once()


def test_timeout_setup_failure_closes_connection(monkeypatch):
    import pytest
    connect = MagicMock()
    monkeypatch.setattr(transport.psycopg2, 'connect', connect)
    connect.return_value.cursor.return_value.__enter__.return_value.execute.side_effect = RuntimeError('failed')
    with pytest.raises(RuntimeError):
        transport.connect_verified('dsn')
    connect.return_value.close.assert_called_once()
