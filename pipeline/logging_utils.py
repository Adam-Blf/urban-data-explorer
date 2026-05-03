"""Logger commun · `log.info` et `log.error` exportés dans des fichiers `.txt`.

Chaque application (feeder/processor/datamart) instancie son propre logger nommé
qui écrit dans `logs/<app>_<run_id>.txt`. Les chemins ne sont jamais codés en
dur, ils proviennent de `Settings.logs_dir`.
"""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from .config import get_settings


def get_logger(app_name: str, run_id: str | None = None) -> logging.Logger:
    """Retourne un logger qui écrit dans `logs/<app>_<run_id>.txt` + stdout.

    Args:
        app_name: nom court (`feeder`, `processor`, `datamart`, `api`).
        run_id: identifiant de run unique (timestamp UTC par défaut).
    """
    settings = get_settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    if run_id is None:
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")

    log_path: Path = settings.logs_dir / f"{app_name}_{run_id}.txt"

    logger = logging.getLogger(f"{app_name}.{run_id}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)sZ | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    logger.info("Logger initialised · log file: %s", log_path)
    return logger


def today_partition() -> str:
    """ISO date `YYYY-MM-DD` utilisée pour le partitionnement courant."""
    return datetime.now(UTC).strftime("%Y-%m-%d")
