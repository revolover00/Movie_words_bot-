from unittest.mock import Mock

import postgres_connection as transport


def test_python_database_tls_cannot_be_disabled_by_url(monkeypatch):
    connect = Mock(return_value=object())
    monkeypatch.setattr(transport.psycopg2, 'connect', connect)
    dsn = 'postgresql://user:password@example.com/db?sslmode=disable'
    assert transport.connect_verified(dsn) is connect.return_value
    args, options = connect.call_args
    assert args == (dsn,)
    assert options['sslmode'] == 'verify-full'
    assert options['sslrootcert'] == transport.certifi.where()
    assert options['connect_timeout'] == 10
    assert options['options'] == '-c statement_timeout=15000'
