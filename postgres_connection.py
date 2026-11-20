"""Shared verified PostgreSQL transport for Python production and integration."""
import certifi
import psycopg2


def connect_verified(dsn):
    # Keyword settings override weaker URL options. Never downgrade on failure.
    conn = psycopg2.connect(dsn, sslmode='verify-full', sslrootcert=certifi.where(),
                            connect_timeout=10)
    try:
        # Transaction poolers reject statement_timeout in startup options.
        with conn.cursor() as cur:
            cur.execute('SET statement_timeout = 15000')
        conn.commit()
        return conn
    except Exception:
        conn.close()
        raise
