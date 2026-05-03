"""Produit un manifeste JSON décrivant un run pipeline · traçabilité / lineage.

Inventaire :
- Date du run, commit Git, hostname
- Pour chaque source · partitions raw/silver présentes (year/month/day)
- Pour chaque table Gold · row count + checksum (md5 du dump CSV partiel)
- Liste des fichiers logs

Sortie · `data/manifests/run_<UTC>.json` (commitable ou archivable).
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SILVER = ROOT / "data" / "silver"
GOLD_DB = ROOT / os.environ.get("GOLD_DUCKDB_PATH", "data/gold/urban.duckdb")
LOGS = ROOT / os.environ.get("LOGS_DIR", "logs")
OUT_DIR = ROOT / "data" / "manifests"


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _scan_layer(root: Path) -> dict[str, list[str]]:
    """Retourne { source: [partition path relative, ...] }."""
    if not root.exists():
        return {}
    out: dict[str, list[str]] = {}
    for source_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        partitions = []
        for f in sorted(source_dir.rglob("*")):
            if f.is_file():
                partitions.append(f.relative_to(root).as_posix())
        if partitions:
            out[source_dir.name] = partitions
    return out


def _gold_summary() -> dict:
    if not GOLD_DB.exists():
        return {"status": "missing", "path": str(GOLD_DB)}
    con = duckdb.connect(GOLD_DB.as_posix(), read_only=True)
    try:
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        out = {"path": str(GOLD_DB.relative_to(ROOT)), "tables": {}}
        for t in tables:
            count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            sample = con.execute(f"SELECT * FROM {t} LIMIT 25").fetchall()
            sample_bytes = json.dumps(sample, default=str, sort_keys=True).encode()
            out["tables"][t] = {
                "row_count": count,
                # MD5 used for non-cryptographic content fingerprinting only.
                "sample_md5": hashlib.md5(sample_bytes, usedforsecurity=False).hexdigest()[:16],
            }
        return out
    finally:
        con.close()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    manifest = {
        "run_id": ts,
        "generated_at_utc": ts,
        "host": socket.gethostname(),
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_branch": _git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "git_dirty": bool(_git(["status", "--porcelain"])),
        "bronze_partitions": _scan_layer(RAW),
        "silver_partitions": _scan_layer(SILVER),
        "gold": _gold_summary(),
        "logs": sorted(p.name for p in LOGS.glob("*.txt")) if LOGS.exists() else [],
    }

    out = OUT_DIR / f"run_{ts}.json"
    out.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print(f"manifest written · {out}")


if __name__ == "__main__":
    main()
