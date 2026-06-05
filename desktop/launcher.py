"""Lanceur tout-en-un Urban Data Explorer (exe local-first).

Sert l'API FastAPI ET le front React builde depuis un seul processus, sur
127.0.0.1:8000, puis ouvre le navigateur. Aucune dependance externe : pas de
Docker, pas de base de donnees, 100% hors ligne (donnees local-first).

Empaquete via `python build.py` (PyInstaller, onefile).
"""

from __future__ import annotations

import os
import sys
import threading
import webbrowser
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def _base_dir() -> Path:
    """Racine des ressources : dossier d'extraction PyInstaller si gele, sinon repo."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[1]


def main() -> None:
    base = _base_dir()
    dist = base / "frontend" / "dist"

    # Active le service de la SPA par l'API (lu a l'import de api.main).
    os.environ.setdefault("UDE_STATIC_DIR", str(dist))
    # Pas de CORS necessaire : front et API sur la meme origine.
    os.environ.setdefault("UDE_CORS_ORIGINS", URL)

    import uvicorn  # noqa: E402  (apres configuration de l'env)

    from api.main import app  # noqa: E402

    threading.Timer(1.5, lambda: webbrowser.open(URL)).start()
    print(f"\n  Urban Data Explorer -> {URL}  (Ctrl+C pour quitter)\n")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
