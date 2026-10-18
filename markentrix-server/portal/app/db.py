"""Datenbankzugriff. Jede Anfrage läuft in einer Transaktion, in der Rolle und Kunde für die
Row-Level-Security gesetzt werden. Die App-Rolle mk_app kann die Trennung nicht umgehen."""
from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from . import config

pool: ConnectionPool | None = None


def open_pool():
    global pool
    pool = ConnectionPool(config.DATABASE_URL, min_size=1, max_size=10, open=True, kwargs={"row_factory": dict_row})
    pool.wait(timeout=30)


def close_pool():
    if pool:
        pool.close()


@contextmanager
def tx(rolle: str, kunden_id=None):
    assert rolle in ("admin", "kunde", "system")
    with pool.connection() as conn:
        with conn.transaction():
            cur = conn.cursor()
            cur.execute(
                "SELECT set_config('app.rolle', %s, true), set_config('app.kunden_id', %s, true)",
                (rolle, str(kunden_id) if kunden_id else ""),
            )
            yield cur
