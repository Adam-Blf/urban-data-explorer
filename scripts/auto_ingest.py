"""Auto-ingestion hebdomadaire des sources Open Data Paris.

Planifie via Windows Task Scheduler (XML) chaque dimanche a 04h00.
Telecharge toutes les sources avec download_url depuis:
  - opendata.paris.fr (API Opendatasoft v2.1)
  - data.gouv.fr (liens directs CSV/GZ)
  - data.education.gouv.fr (API Opendatasoft v2.1)
  - OpenStreetMap Overpass API (OVERPASS: prefix)

Usage:
  python scripts/auto_ingest.py [--source SOURCE_ID] [--dry-run]
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = ROOT / "data" / "raw" / "downloads"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("auto_ingest")

OVERPASS_API = "https://overpass-api.de/api/interpreter"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "urban-data-explorer/1.0 (+https://github.com/Adam-Blf/urban-data-explorer)"})


def _download_http(url: str, dest: Path, retries: int = 3, delay: float = 5.0) -> bool:
    """Download via HTTP GET with retry logic."""
    for attempt in range(1, retries + 1):
        try:
            resp = SESSION.get(url, timeout=120, stream=True)
            resp.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        fh.write(chunk)
            size_kb = dest.stat().st_size // 1024
            log.info("OK %s (%d KB)", dest.name, size_kb)
            return True
        except Exception as exc:
            log.warning("Attempt %d/%d failed for %s: %s", attempt, retries, dest.name, exc)
            if attempt < retries:
                time.sleep(delay * attempt)
    return False


def _download_overpass(query: str, dest: Path, retries: int = 3) -> bool:
    """POST Overpass QL query and save TSV result."""
    for attempt in range(1, retries + 1):
        try:
            resp = SESSION.post(OVERPASS_API, data={"data": query}, timeout=120)
            resp.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.content)
            size_kb = dest.stat().st_size // 1024
            log.info("OK OSM %s (%d KB)", dest.name, size_kb)
            return True
        except Exception as exc:
            log.warning("Attempt %d/%d OSM failed for %s: %s", attempt, retries, dest.name, exc)
            if attempt < retries:
                time.sleep(10 * attempt)
    return False


def ingest_source(source_id: str, download_url: str, dry_run: bool = False) -> bool:
    """Download one source. Returns True on success."""
    if not download_url:
        log.warning("No download_url for %s, skipping", source_id)
        return False

    ext = ".tsv" if download_url.startswith("OVERPASS:") else ".csv"
    if download_url.endswith(".gz"):
        ext = ".csv.gz"

    dest = DOWNLOAD_DIR / f"{source_id}{ext}"

    if dry_run:
        log.info("[DRY-RUN] Would download %s -> %s", source_id, dest.name)
        return True

    if download_url.startswith("OVERPASS:"):
        query = download_url[len("OVERPASS:"):]
        return _download_overpass(query, dest)
    else:
        return _download_http(download_url, dest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Urban Data Explorer - weekly auto-ingestion")
    parser.add_argument("--source", help="Ingest only this source_id")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be downloaded, no writes")
    args = parser.parse_args(argv)

    try:
        from etl.bronze.catalog import ALL_SOURCES
    except ImportError:
        sys.path.insert(0, str(ROOT))
        from etl.bronze.catalog import ALL_SOURCES

    targets = [s for s in ALL_SOURCES if not s.metadata_only]
    if args.source:
        targets = [s for s in targets if s.source_id == args.source]
        if not targets:
            log.error("Unknown source_id: %s", args.source)
            return 1

    log.info("Starting ingestion of %d sources", len(targets))
    ok, fail = 0, 0
    for spec in targets:
        success = ingest_source(spec.source_id, spec.download_url, dry_run=args.dry_run)
        if success:
            ok += 1
        else:
            fail += 1
        time.sleep(0.5)  # polite rate-limiting

    log.info("Done: %d ok, %d failed", ok, fail)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
