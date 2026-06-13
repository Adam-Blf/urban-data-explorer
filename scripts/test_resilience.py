"""Test de résilience – C1.4 : dégradation gracieuse si PostgreSQL tombe.

Usage :
    python scripts/test_resilience.py

Prérequis :
    - Docker en cours d'exécution
    - L'API lancée séparément : uvicorn api.main:app --reload

Si Docker est absent ou l'API n'est pas accessible, le script affiche un
message explicatif et se termine proprement (code 0).

Note : ce script utilise uniquement subprocess (docker CLI) et requests,
conformément à la contrainte EDR qui interdit les fichiers .bat/.ps1.
"""

from __future__ import annotations

import subprocess
import sys
import time

try:
    import requests as _req
except ImportError:
    print("[SKIP] Le module 'requests' est requis. Installez-le via pip.")
    sys.exit(0)

API_URL = "http://localhost:8000"
# Nom du conteneur PostgreSQL tel que défini dans docker-compose.yml
# (docker-compose nomme par défaut : <dossier>-<service>-1)
PG_CONTAINER = "urban-data-explorer-postgres-1"
HTTP_TIMEOUT = 5  # secondes


def docker_available() -> bool:
    """Vérifie si le daemon Docker répond."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def api_healthy() -> bool:
    """Vérifie que l'endpoint /health retourne 200."""
    try:
        r = _req.get(f"{API_URL}/health", timeout=HTTP_TIMEOUT)
        return r.status_code == 200
    except _req.RequestException:
        return False


def docker_stop(container: str) -> bool:
    r = subprocess.run(["docker", "stop", container], capture_output=True, timeout=30)
    return r.returncode == 0


def docker_start(container: str) -> bool:
    r = subprocess.run(["docker", "start", container], capture_output=True, timeout=30)
    return r.returncode == 0


def main() -> int:
    print("=" * 60)
    print("  Test de résilience – C1.4")
    print("=" * 60)

    # ── 1. Vérifier Docker ───────────────────────────────────────────────
    if not docker_available():
        print("\n  [SKIP] Docker n'est pas accessible.")
        print("  Lancez Docker Desktop puis réessayez.")
        return 0

    # ── 2. Vérifier l'API ────────────────────────────────────────────────
    if not api_healthy():
        print(f"\n  [SKIP] L'API n'est pas accessible à {API_URL}.")
        print("  Lancez d'abord : uvicorn api.main:app --reload")
        return 0

    print(f"\n  1. API accessible à {API_URL}  [OK]")

    # ── 3. Arrêter PostgreSQL ────────────────────────────────────────────
    print(f"  2. Arrêt du conteneur PostgreSQL ({PG_CONTAINER})...")
    stopped = docker_stop(PG_CONTAINER)
    if not stopped:
        print(
            f"     [WARN] Impossible d'arrêter {PG_CONTAINER}. "
            "Conteneur absent ou déjà arrêté – poursuite du test."
        )
    time.sleep(2)  # laisser le temps au pool de connexions de détecter la coupure

    # ── 4. Dégradation gracieuse ─────────────────────────────────────────
    print("  3. Vérification de la dégradation gracieuse...")
    healthy_after_stop = api_healthy()
    if healthy_after_stop:
        print("     [OK] L'API répond en mode fallback (parquet local).")
    else:
        print("     [FAIL] L'API ne répond plus après l'arrêt de PostgreSQL.")

    # ── 5. Relancer PostgreSQL ───────────────────────────────────────────
    print(f"  4. Redémarrage de PostgreSQL ({PG_CONTAINER})...")
    docker_start(PG_CONTAINER)

    # ── 6. Mesure du temps de récupération ───────────────────────────────
    print("  5. Mesure du temps de récupération (max 30s)...")
    t_start = time.monotonic()
    recovered = False
    for _ in range(30):
        time.sleep(1)
        if api_healthy():
            recovered = True
            break
    recovery_time_s = time.monotonic() - t_start

    # ── 7. Rapport ───────────────────────────────────────────────────────
    print("\n  --- Rapport de résilience ---")
    print(f"  API après coupure PostgreSQL : {'OK' if healthy_after_stop else 'FAIL'}")
    if recovered:
        print(f"  Temps de récupération        : {recovery_time_s:.1f}s")
    else:
        print("  Récupération                 : timeout (>30s)")

    return 0 if healthy_after_stop else 1


if __name__ == "__main__":
    sys.exit(main())
