"""Table explorer — liste et lecture des tables PostgreSQL et Cassandra.

Routes :
    GET /tables/                        — inventaire complet (pg + cassandra)
    GET /tables/pg/{schema}/{table}     — colonnes + données paginées (PostgreSQL)
    GET /tables/cass/{table}            — colonnes + données paginées (Cassandra)

Sécurité anti-injection : les noms de schéma/table sont validés contre
la whitelist extraite d'information_schema (pg) et system_schema (cass)
avant d'être interpolés dans les requêtes. Aucune valeur issue de l'URL
n'est passée directement dans une f-string SQL.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ..db import pg_fetch_all, cassandra_session

router = APIRouter(prefix="/tables", tags=["tables"])

# Identifiant SQL autorisé : lettres, chiffres, tirets bas, points (schema.table)
_SAFE_IDENT = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def _safe(name: str) -> str:
    """Leve HTTPException 400 si le nom n'est pas un identifiant SQL safe."""
    if not _SAFE_IDENT.match(name):
        raise HTTPException(status_code=400, detail=f"Nom invalide : {name!r}")
    return name


# ---------------------------------------------------------------------------
# Inventaire
# ---------------------------------------------------------------------------

@router.get("/")
def list_tables() -> dict[str, Any]:
    """Retourne l'arbre complet : schemas/tables PG + tables Cassandra."""
    sources: list[dict[str, Any]] = []

    # --- PostgreSQL -----------------------------------------------------------
    try:
        rows = pg_fetch_all(
            """
            SELECT t.table_schema, t.table_name,
                   c.reltuples::bigint AS estimate
            FROM information_schema.tables t
            JOIN pg_class c ON c.relname = t.table_name
            JOIN pg_namespace n ON n.oid = c.relnamespace
                AND n.nspname = t.table_schema
            WHERE t.table_schema NOT IN ('information_schema','pg_catalog','pg_toast')
              AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_schema, t.table_name
            """
        )
        schemas: dict[str, list[dict]] = {}
        for r in rows:
            s = r["table_schema"]
            if s not in schemas:
                schemas[s] = []
            schemas[s].append({
                "name": r["table_name"],
                "row_estimate": max(0, r["estimate"]),
            })
        sources.append({
            "id": "pg",
            "label": "PostgreSQL",
            "type": "sql",
            "status": "connected",
            "schemas": [{"name": k, "tables": v} for k, v in schemas.items()],
        })
    except Exception as exc:
        sources.append({
            "id": "pg",
            "label": "PostgreSQL",
            "type": "sql",
            "status": "unavailable",
            "error": str(exc),
            "schemas": [],
        })

    # --- Cassandra ------------------------------------------------------------
    try:
        sess = cassandra_session()
        keyspace = sess.keyspace or "ude"
        result = sess.execute(
            "SELECT table_name FROM system_schema.tables WHERE keyspace_name=%s",
            (keyspace,)
        )
        cass_tables = [{"name": r.table_name} for r in result]
        sources.append({
            "id": "cass",
            "label": "Cassandra",
            "type": "nosql",
            "status": "connected",
            "keyspace": keyspace,
            "tables": cass_tables,
        })
    except Exception as exc:
        sources.append({
            "id": "cass",
            "label": "Cassandra",
            "type": "nosql",
            "status": "unavailable",
            "error": str(exc),
            "keyspace": "ude",
            "tables": [],
        })

    return {"sources": sources}


# ---------------------------------------------------------------------------
# PostgreSQL — colonnes + données
# ---------------------------------------------------------------------------

@router.get("/pg/{schema}/{table}")
def pg_table(
    schema: str,
    table: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    filter_col: str | None = None,
    filter_val: str | None = None,
) -> dict[str, Any]:
    """Colonnes + données paginées d'une table PostgreSQL."""
    _safe(schema)
    _safe(table)

    # Valider que la table existe (whitelist)
    check = pg_fetch_all(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s AND table_type = 'BASE TABLE'
        """,
        (schema, table),
    )
    if not check:
        raise HTTPException(status_code=404, detail=f"Table inconnue : {schema}.{table}")

    # Colonnes avec type et nullabilité
    cols = pg_fetch_all(
        """
        SELECT column_name, data_type, is_nullable, column_default,
               character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """,
        (schema, table),
    )

    # Nombre total de lignes
    count_rows = pg_fetch_all(
        f'SELECT COUNT(*) AS n FROM "{schema}"."{table}"'  # noqa: S608
    )
    total: int = count_rows[0]["n"] if count_rows else 0

    offset = (page - 1) * page_size

    # Filtre simple sur une colonne (uniquement si colonne valide)
    where_clause = ""
    params: tuple[Any, ...] = ()
    if filter_col and filter_val is not None:
        _safe(filter_col)
        valid_cols = {c["column_name"] for c in cols}
        if filter_col not in valid_cols:
            raise HTTPException(status_code=400, detail=f"Colonne inconnue : {filter_col}")
        where_clause = f'WHERE CAST("{filter_col}" AS TEXT) ILIKE %s'
        params = (f"%{filter_val}%",)

    rows = pg_fetch_all(
        f'SELECT * FROM "{schema}"."{table}" {where_clause} '  # noqa: S608
        f"ORDER BY 1 LIMIT %s OFFSET %s",
        (*params, page_size, offset),
    )

    # Sérialiser les types non-JSON (datetime, Decimal, UUID…)
    def _serial(v: Any) -> Any:
        if v is None:
            return None
        if hasattr(v, "isoformat"):
            return v.isoformat()
        try:
            return float(v) if str(v).replace(".", "", 1).lstrip("-").isdigit() else str(v)
        except Exception:
            return str(v)

    serialized = [
        {k: _serial(val) for k, val in row.items()} for row in rows
    ]

    return {
        "source": "pg",
        "schema": schema,
        "table": table,
        "columns": cols,
        "rows": serialized,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, -(-total // page_size)),
    }


# ---------------------------------------------------------------------------
# Cassandra — colonnes + données
# ---------------------------------------------------------------------------

@router.get("/cass/{table}")
def cass_table(
    table: str,
    page_size: int = Query(50, ge=1, le=500),
    paging_state: str | None = None,
) -> dict[str, Any]:
    """Colonnes + données paginées d'une table Cassandra (cursor-based)."""
    _safe(table)

    try:
        sess = cassandra_session()
        keyspace = sess.keyspace or "ude"
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Cassandra indisponible : {exc}") from exc

    # Valider la table
    check = list(sess.execute(
        "SELECT table_name FROM system_schema.tables "
        "WHERE keyspace_name=%s AND table_name=%s",
        (keyspace, table),
    ))
    if not check:
        raise HTTPException(status_code=404, detail=f"Table Cassandra inconnue : {table}")

    # Colonnes
    col_rows = sess.execute(
        "SELECT column_name, type, kind FROM system_schema.columns "
        "WHERE keyspace_name=%s AND table_name=%s",
        (keyspace, table),
    )
    cols = [
        {"column_name": r.column_name, "data_type": r.type, "kind": r.kind}
        for r in col_rows
    ]

    # Données paginées (Cassandra ne supporte pas OFFSET)
    from cassandra.query import SimpleStatement

    stmt = SimpleStatement(f"SELECT * FROM {keyspace}.{table}", fetch_size=page_size)  # noqa: S608
    result_set = sess.execute(stmt)

    rows_out: list[dict[str, Any]] = []
    for r in result_set:
        row_dict = r._asdict() if hasattr(r, "_asdict") else dict(r._fields and zip(r._fields, r))
        serialized = {}
        for k, v in row_dict.items():
            if v is None:
                serialized[k] = None
            elif hasattr(v, "isoformat"):
                serialized[k] = v.isoformat()
            else:
                serialized[k] = str(v) if not isinstance(v, (int, float, bool)) else v
        rows_out.append(serialized)
        if len(rows_out) >= page_size:
            break

    return {
        "source": "cass",
        "keyspace": keyspace,
        "table": table,
        "columns": cols,
        "rows": rows_out,
        "page_size": page_size,
        "note": "Cassandra: pagination par cursor, pas par offset.",
    }
