"""Shared verified PostgreSQL transport for Python production and integration."""
import certifi
import psycopg2


def connect_verified(dsn):
    # Keyword settings override weaker URL options. Never downgrade on failure.
    return psycopg2.connect(dsn, sslmode='verify-full', sslrootcert=certifi.where(),
                            connect_timeout=10, options='-c statement_timeout=15000')
