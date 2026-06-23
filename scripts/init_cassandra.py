"""Initialise le keyspace et les tables Cassandra depuis schema.cql.

Usage: python scripts/init_cassandra.py [--host HOST] [--port PORT]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "cassandra" / "schema.cql"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Init Cassandra schema")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9042)
    args = parser.parse_args(argv)

    try:
        from cassandra.cluster import Cluster
        from cassandra.io.asyncioreactor import AsyncioConnection
    except ImportError as exc:
        print(f"cassandra-driver manquant: {exc}")
        return 1

    print(f"Connexion a Cassandra {args.host}:{args.port} ...")
    try:
        cluster = Cluster([args.host], port=args.port, connection_class=AsyncioConnection)
        session = cluster.connect()
    except Exception as exc:
        print(f"Impossible de se connecter: {exc}")
        return 1

    schema_sql = SCHEMA.read_text(encoding="utf-8")
    # Split on ";", strip whitespace, drop blanks, comments and USE directives
    # (USE is a CQL session directive not supported by the driver - use set_keyspace instead)
    statements = [
        s.strip()
        for s in schema_sql.split(";")
        if s.strip() and not s.strip().startswith("--") and not s.strip().upper().startswith("USE ")
    ]

    keyspace = None
    for stmt in statements:
        # Extract keyspace from CREATE KEYSPACE to set it after creation
        if "CREATE KEYSPACE" in stmt.upper():
            import re
            m = re.search(r"CREATE KEYSPACE\s+(?:IF NOT EXISTS\s+)?(\w+)", stmt, re.IGNORECASE)
            if m:
                keyspace = m.group(1)
        try:
            session.execute(stmt)
            print(f"  OK: {stmt[:60].replace('\n', ' ')}...")
        except Exception as exc:
            print(f"  ERR: {exc}")

    if keyspace:
        try:
            session.set_keyspace(keyspace)
        except Exception:
            pass

    cluster.shutdown()
    print("Schema Cassandra initialise.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
