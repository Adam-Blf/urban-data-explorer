"""Construit l'executable Windows tout-en-un Urban Data Explorer.

Etapes :
  1. build du front React en mode "meme origine" (VITE_API_BASE vide) -> frontend/dist
  2. PyInstaller onefile empaquetant le launcher + l'API + le front + les donnees
     local-first (geojson multi-niveaux, parquet Gold).

Usage : python build.py
Sortie : dist/ude.exe (double-clic = lance l'API + le front + ouvre le navigateur)

Conforme aux contraintes EDR : build via Python uniquement, aucun .bat / .ps1.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
SEP = os.pathsep  # ';' sous Windows, ':' sous Unix

# Donnees local-first a embarquer : (source, dossier cible relatif dans l'exe)
DATA_ASSETS = [
    (ROOT / "data" / "raw" / "downloads" / "paris_city.geojson", "data/raw/downloads"),
    (ROOT / "data" / "raw" / "downloads" / "paris_arrondissements.geojson", "data/raw/downloads"),
    (ROOT / "data" / "raw" / "downloads" / "paris_iris.geojson", "data/raw/downloads"),
    (ROOT / "data" / "raw" / "downloads" / "paris_streets.geojson", "data/raw/downloads"),
    (ROOT / "data" / "raw" / "downloads" / "paris_buildings.geojson", "data/raw/downloads"),
    (ROOT / "data" / "gold" / "dashboard.parquet", "data/gold"),
    (ROOT / "data" / "gold" / "timeline.parquet", "data/gold"),
]


def _run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> None:
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def _npm() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def build_frontend() -> None:
    print("== 1/2 · build du front (VITE_API_BASE vide = meme origine) ==")
    env = os.environ.copy()
    env["VITE_API_BASE"] = ""  # exe -> API et front sur la meme origine
    if not (FRONTEND / "node_modules").is_dir():
        _run([_npm(), "install"], cwd=FRONTEND, env=env)
    _run([_npm(), "run", "build"], cwd=FRONTEND, env=env)
    if not (DIST / "index.html").is_file():
        sys.exit("Echec : frontend/dist/index.html introuvable apres le build.")


def build_exe() -> None:
    print("== 2/2 · empaquetage PyInstaller (onefile) ==")
    missing = [str(src) for src, _ in DATA_ASSETS if not src.is_file()]
    if missing:
        sys.exit("Donnees manquantes :\n  " + "\n  ".join(missing))

    add_data = [f"{DIST}{SEP}frontend/dist"]
    add_data += [f"{src}{SEP}{dest}" for src, dest in DATA_ASSETS]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile",
        "--name", "ude",
        "--collect-all", "uvicorn",
        "--collect-submodules", "etl",
        "--collect-submodules", "api",
        # drivers DB inutiles en local-first (imports differes, geres a l'exec)
        "--exclude-module", "cassandra",
        "--exclude-module", "kafka",
    ]
    for entry in add_data:
        cmd += ["--add-data", entry]
    cmd.append(str(ROOT / "desktop" / "launcher.py"))

    _run(cmd, cwd=ROOT)
    exe = ROOT / "dist" / ("ude.exe" if os.name == "nt" else "ude")
    print(f"\n  OK -> {exe}\n  Double-clic pour lancer l'application.\n")


def main() -> None:
    if shutil.which(_npm()) is None:
        sys.exit("npm introuvable : installe Node.js avant de builder le front.")
    build_frontend()
    build_exe()


if __name__ == "__main__":
    main()
