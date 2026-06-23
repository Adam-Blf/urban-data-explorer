"""Connexions aux bases de données – PostgreSQL et Cassandra.

Les imports lourds (cassandra-driver) sont différés pour permettre
le démarrage local-first sans conteneurs Docker.
"""

from __future__ import annotations

import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor


@contextmanager
def pg_conn():
    """Open a PostgreSQL connection using environment variables."""
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "ude"),
        user=os.getenv("POSTGRES_USER", "ude"),
        password=os.getenv("POSTGRES_PASSWORD", "ude"),
    )
    try:
        yield conn
    finally:
        conn.close()


def pg_fetch_all(sql: str, params: tuple[object, ...] | None = None):
    """Execute a read query and return dictionaries."""
    with pg_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]


def pg_execute(sql: str, params: tuple[object, ...] | None = None) -> None:
    """Execute a write query (INSERT / UPDATE / DDL) and commit."""
    with pg_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
        conn.commit()


_cass_cluster = None
_cass_session = None


def cassandra_session():
    """Return a module-level Cassandra session (lazy singleton).

    Uses AsyncioConnection for Python 3.12 compatibility (asyncore was removed).
    Creates the cluster once; subsequent calls reuse the connection pool.
    """
    global _cass_cluster, _cass_session
    if _cass_session is None:
        from cassandra.cluster import Cluster
        from cassandra.io.asyncioreactor import AsyncioConnection

        host = os.getenv("CASSANDRA_HOST", "cassandra")
        port = int(os.getenv("CASSANDRA_PORT", "9042"))
        keyspace = os.getenv("CASSANDRA_KEYSPACE", "ude")
        _cass_cluster = Cluster([host], port=port, connection_class=AsyncioConnection)
        _cass_session = _cass_cluster.connect(keyspace)
    return _cass_session
