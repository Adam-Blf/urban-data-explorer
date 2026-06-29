"""Lanceur de soutenance — Urban Data Explorer.

Lance toute la stack (Docker, ETL, API, Frontend), ouvre le PowerPoint
et les onglets navigateur nécessaires à la soutenance RNCP40875 Bloc 1.

Usage : python lancer_soutenance.py [--sans-ingestion] [--sans-streaming]
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import textwrap
import threading
import time
import webbrowser
from pathlib import Path

# ── Répertoire racine ──────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent

# ── Palette ANSI (sans dépendances) ───────────────────────────────────────
R = "\033[0m"          # reset
BOLD = "\033[1m"
BLUE = "\033[38;2;22;55;103m"      # #163767 EFREI bleu
CYAN = "\033[38;2;12;120;180m"     # #0C78B4
PINK = "\033[38;2;255;67;184m"     # #FF43B8
GREEN = "\033[38;2;16;185;129m"    # success
YELLOW = "\033[38;2;245;158;11m"   # warning
RED = "\033[38;2;239;68;68m"       # error
DIM = "\033[2m"

# ── Icônes Unicode ─────────────────────────────────────────────────────────
OK = f"{GREEN}✔{R}"
WAIT = f"{YELLOW}⏳{R}"
FAIL = f"{RED}✘{R}"
INFO = f"{CYAN}ℹ{R}"
ARROW = f"{PINK}▶{R}"

# ── URLs exposées ──────────────────────────────────────────────────────────
URL_FRONTEND  = "http://localhost:5173"
URL_SWAGGER   = "http://localhost:8000/docs"
URL_HEALTH    = "http://localhost:8000/health"
URL_PROMETHEUS = "http://localhost:9090"
URL_GRAFANA   = "http://localhost:3000"


# ──────────────────────────────────────────────────────────────────────────
# Helpers d'affichage
# ──────────────────────────────────────────────────────────────────────────

def _clear():
    os.system("cls" if platform.system() == "Windows" else "clear")


def banner():
    _clear()
    print(f"""
{BLUE}{BOLD}╔══════════════════════════════════════════════════════════════════╗
║          URBAN DATA EXPLORER — LANCEUR DE SOUTENANCE             ║
║          RNCP40875 · Bloc 1 · Expert Ingénierie des Données      ║
╚══════════════════════════════════════════════════════════════════╝{R}
{DIM}  Adam Beloucif & Émilien Morice · EFREI Paris Panthéon-Assas{R}
""")


def step(label: str, status: str = WAIT):
    print(f"  {status}  {label}")


def ok(label: str):
    print(f"  {OK}  {label}")


def warn(label: str):
    print(f"  {YELLOW}⚠{R}  {label}")


def err(label: str):
    print(f"  {FAIL}  {RED}{label}{R}")


def section(title: str):
    print(f"\n{CYAN}{BOLD}── {title}{R}")


def separator():
    print(f"\n{DIM}{'─' * 66}{R}\n")


# ──────────────────────────────────────────────────────────────────────────
# Vérification des prérequis
# ──────────────────────────────────────────────────────────────────────────

def check_prereqs() -> dict[str, bool]:
    section("Vérification des prérequis")
    checks = {
        "docker": shutil.which("docker") is not None,
        "docker_compose": (
            shutil.which("docker-compose") is not None
            or _docker_compose_v2_ok()
        ),
        "python": sys.version_info >= (3, 11),
        "npm": shutil.which("npm") is not None,
    }
    labels = {
        "docker": "Docker",
        "docker_compose": "Docker Compose",
        "python": f"Python ≥ 3.11 (actuel : {sys.version.split()[0]})",
        "npm": "npm (frontend)",
    }
    for k, v in checks.items():
        (ok if v else warn)(labels[k])
    return checks


def _docker_compose_v2_ok() -> bool:
    try:
        r = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True, timeout=5
        )
        return r.returncode == 0
    except Exception:
        return False


def _compose_cmd() -> list[str]:
    """Retourne la commande docker compose disponible."""
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    return ["docker", "compose"]


# ──────────────────────────────────────────────────────────────────────────
# Docker
# ──────────────────────────────────────────────────────────────────────────

def start_docker_core():
    section("Démarrage des services core (PostgreSQL + Cassandra)")
    step("docker compose up -d postgres cassandra cassandra-init ...")

    cmd = _compose_cmd() + [
        "-f", str(ROOT / "docker-compose.yml"),
        "up", "-d", "--wait",
        "postgres", "cassandra", "cassandra-init",
    ]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        # --wait non supporté sur les vieilles versions → relancer sans
        cmd_no_wait = [c for c in cmd if c != "--wait"]
        result = subprocess.run(cmd_no_wait, cwd=ROOT, capture_output=True, text=True)

    if result.returncode == 0:
        ok("PostgreSQL 16 (pgvector)  →  :5432")
        ok("Cassandra 4.1             →  :9042")
    else:
        err("Échec du démarrage des services core")
        print(DIM + result.stderr[-800:] + R)
        _prompt_continue()


def start_docker_streaming():
    section("Démarrage du streaming (Zookeeper + Kafka + Producteurs)")
    step("docker compose --profile streaming up -d ...")

    cmd = _compose_cmd() + [
        "-f", str(ROOT / "docker-compose.yml"),
        "--profile", "streaming",
        "up", "-d",
        "zookeeper", "kafka", "velib-producer", "consumer",
    ]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)

    if result.returncode == 0:
        ok("Zookeeper  →  :2181")
        ok("Kafka 3.7  →  :9092  (topic ude-events, ude-velib)")
        ok("Producteur Vélib' (snapshots toutes les 30 s)")
        ok("Consommateur Kafka → Cassandra (TTL 7 jours)")
    else:
        warn("Streaming non disponible (image Docker absente ?)  — mode dégradé OK")
        print(DIM + result.stderr[-400:] + R)


def wait_postgres_healthy(timeout: int = 120):
    section("Attente PostgreSQL healthy")
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = subprocess.run(
            _compose_cmd() + [
                "-f", str(ROOT / "docker-compose.yml"),
                "exec", "-T", "postgres",
                "pg_isready", "-U", "ude", "-d", "ude",
            ],
            capture_output=True, cwd=ROOT,
        )
        if r.returncode == 0:
            ok("PostgreSQL prêt")
            return
        print(f"  {WAIT}  En attente de PostgreSQL…", end="\r")
        time.sleep(5)
    warn("PostgreSQL lent à démarrer — on continue quand même")


def wait_cassandra_healthy(timeout: int = 180):
    section("Attente Cassandra healthy")
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = subprocess.run(
            _compose_cmd() + [
                "-f", str(ROOT / "docker-compose.yml"),
                "exec", "-T", "cassandra",
                "cqlsh", "-e", "describe keyspaces",
            ],
            capture_output=True, cwd=ROOT,
        )
        if r.returncode == 0:
            ok("Cassandra prêt — keyspace ude_streaming présent")
            return
        print(f"  {WAIT}  Cassandra démarre (peut prendre ~90 s)…", end="\r")
        time.sleep(10)
    warn("Cassandra lent — on continue (mode dégradé activé automatiquement)")


# ──────────────────────────────────────────────────────────────────────────
# Pipeline ETL
# ──────────────────────────────────────────────────────────────────────────

def run_etl(skip_download: bool = False):
    section("Pipeline ETL — Bronze → Silver → Gold")

    bronze = ROOT / "data" / "raw" / "downloads"
    has_data = bronze.exists() and any(bronze.iterdir()) if bronze.exists() else False

    if not has_data and not skip_download:
        step("Téléchargement des sources Open Data (83 sources)…")
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "auto_ingest.py")],
            cwd=ROOT,
        )
        if r.returncode != 0:
            warn("Téléchargement partiel — on poursuit avec ce qui est disponible")
    elif has_data:
        ok(f"Sources déjà présentes dans data/raw/downloads/ ({len(list(bronze.iterdir()))} fichiers)")

    step("Transformation Bronze → Silver → Gold (Polars)…")
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_pipeline.py")],
        cwd=ROOT,
    )
    if r.returncode == 0:
        ok("Gold Parquet généré  →  data/gold/dashboard.parquet + timeline.parquet")
    else:
        warn("Pipeline ETL partiel — l'API utilisera les données de référence intégrées")


# ──────────────────────────────────────────────────────────────────────────
# API FastAPI
# ──────────────────────────────────────────────────────────────────────────

_api_proc: subprocess.Popen | None = None


def start_api():
    global _api_proc
    section("Démarrage de l'API FastAPI")
    step("uvicorn api.main:app --reload --port 8000")

    env = os.environ.copy()
    env.setdefault("UDE_CORS_ORIGINS", f"{URL_FRONTEND},http://127.0.0.1:5173")

    _api_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app",
         "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # Attendre que l'API réponde
    _wait_http(URL_HEALTH, label="API FastAPI", timeout=30)


def _wait_http(url: str, label: str, timeout: int = 30):
    import urllib.request
    import urllib.error
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            ok(f"{label}  →  {url.replace('/health', '')}")
            return
        except Exception:
            print(f"  {WAIT}  Attente {label}…", end="\r")
            time.sleep(2)
    warn(f"{label} non joignable après {timeout}s — vérifiez les logs")


# ──────────────────────────────────────────────────────────────────────────
# Frontend React
# ──────────────────────────────────────────────────────────────────────────

_front_proc: subprocess.Popen | None = None


def start_frontend():
    global _front_proc
    section("Démarrage du Frontend React (Vite)")

    front_dir = ROOT / "frontend"
    node_modules = front_dir / "node_modules"

    if not node_modules.exists():
        step("npm install (première fois)…")
        subprocess.run(["npm", "install"], cwd=front_dir, check=False)

    step("npm run dev  →  http://localhost:5173")
    _front_proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host"],
        cwd=front_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    _wait_http(URL_FRONTEND, label="Frontend React", timeout=30)


# ──────────────────────────────────────────────────────────────────────────
# Ouverture des onglets et du PPT
# ──────────────────────────────────────────────────────────────────────────

def open_browser_tabs():
    section("Ouverture des onglets navigateur")
    tabs = [
        (URL_FRONTEND,  "Dashboard  (carte 2D/3D)"),
        (URL_SWAGGER,   "Swagger  /docs  (API FastAPI)"),
    ]
    for url, label in tabs:
        webbrowser.open_new_tab(url)
        ok(f"{label}  →  {url}")
        time.sleep(0.5)


def open_pptx():
    section("Ouverture du support de soutenance")
    pptx = ROOT / "soutenance.pptx"
    if not pptx.exists():
        warn("soutenance.pptx introuvable — régénération…")
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_slides_pptx.py")],
            cwd=ROOT,
        )
        if r.returncode != 0:
            err("Impossible de générer soutenance.pptx")
            return

    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(str(pptx))
        elif system == "Darwin":
            subprocess.Popen(["open", str(pptx)])
        else:
            subprocess.Popen(["xdg-open", str(pptx)])
        ok(f"soutenance.pptx ouvert")
    except Exception as e:
        warn(f"Ouverture automatique échouée ({e}) — ouvrez manuellement : {pptx}")


# ──────────────────────────────────────────────────────────────────────────
# Tableau de statut final
# ──────────────────────────────────────────────────────────────────────────

def print_status_table():
    separator()
    print(f"{BOLD}{BLUE}  STACK OPÉRATIONNELLE — LIENS UTILES{R}\n")
    rows = [
        ("Dashboard (carte 2D/3D)",    URL_FRONTEND,            "React + MapLibre/Mapbox"),
        ("API REST (Swagger)",          URL_SWAGGER,             "FastAPI · JWT · Quotas"),
        ("Health check",               URL_HEALTH,              "JSON status"),
        ("Prometheus (monitoring)",     URL_PROMETHEUS,          "profil monitoring"),
        ("Grafana (dashboards)",        URL_GRAFANA,             "admin / admin"),
        ("PostgreSQL",                  "localhost:5432",        "ude / ude / ude"),
        ("Cassandra",                   "localhost:9042",        "keyspace ude_streaming"),
        ("Kafka",                       "localhost:9092",        "topics: ude-events, ude-velib"),
    ]
    print(f"  {'Service':<30}  {'URL / Host':<35}  {DIM}Détail{R}")
    print(f"  {'─'*30}  {'─'*35}  {'─'*20}")
    for name, url, detail in rows:
        print(f"  {CYAN}{name:<30}{R}  {url:<35}  {DIM}{detail}{R}")

    separator()
    print(f"  {INFO}  Comptes de démo  :  {BOLD}demo/demo{R} (viewer)  ·  {BOLD}admin/admin{R} (admin)")
    print(f"  {INFO}  Arrêter la stack :  {BOLD}Ctrl+C{R}  puis  "
          f"{BOLD}docker compose down{R}")
    separator()


# ──────────────────────────────────────────────────────────────────────────
# Boucle de supervision (garde le script vivant + affiche les logs API)
# ──────────────────────────────────────────────────────────────────────────

def _stream_logs(proc: subprocess.Popen, prefix: str, color: str = DIM):
    """Lit stdout d'un sous-processus et préfixe chaque ligne."""
    if proc is None or proc.stdout is None:
        return
    for line in proc.stdout:
        decoded = line.decode("utf-8", errors="replace").rstrip()
        if decoded:
            print(f"{color}[{prefix}]{R} {DIM}{decoded}{R}")


def keep_alive():
    """Stream logs API + gère l'arrêt propre sur Ctrl+C."""
    print(f"\n  {INFO}  {DIM}Appuyez sur Ctrl+C pour arrêter toute la stack.{R}\n")

    # Thread de logs API en fond
    if _api_proc:
        t = threading.Thread(
            target=_stream_logs, args=(_api_proc, "API", CYAN), daemon=True
        )
        t.start()

    try:
        while True:
            # Vérifier que les processus sont toujours vivants
            if _api_proc and _api_proc.poll() is not None:
                warn("L'API s'est arrêtée inopinément — relancez le script")
                break
            if _front_proc and _front_proc.poll() is not None:
                warn("Le Frontend s'est arrêté inopinément — relancez le script")
                break
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}Arrêt demandé…{R}")
        _shutdown()


def _shutdown():
    for proc in (_front_proc, _api_proc):
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    print(f"  {OK}  Processus locaux arrêtés.")
    print(f"  {INFO}  Pour arrêter Docker :  {BOLD}docker compose down{R}")
    print(f"  {INFO}  Pour tout supprimer :  {BOLD}docker compose down -v{R}\n")


# ──────────────────────────────────────────────────────────────────────────
# Utilitaire
# ──────────────────────────────────────────────────────────────────────────

def _prompt_continue():
    try:
        input(f"\n  {YELLOW}Appuyez sur Entrée pour continuer malgré l'erreur…{R}")
    except (EOFError, KeyboardInterrupt):
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────
# Point d'entrée
# ──────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Lance toute la stack Urban Data Explorer pour la soutenance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Exemples :
              python lancer_soutenance.py                   # stack complète
              python lancer_soutenance.py --sans-ingestion  # skip téléchargement
              python lancer_soutenance.py --sans-streaming  # skip Kafka/Vélib
              python lancer_soutenance.py --api-seulement   # API + front seulement
        """),
    )
    parser.add_argument("--sans-ingestion", action="store_true",
                        help="Ne pas télécharger les sources (données déjà présentes)")
    parser.add_argument("--sans-streaming", action="store_true",
                        help="Ne pas démarrer Kafka/Zookeeper/Producteurs")
    parser.add_argument("--api-seulement", action="store_true",
                        help="Lance seulement l'API + le frontend (Docker déjà up)")
    args = parser.parse_args()

    banner()

    # ── 0. Prérequis ──────────────────────────────────────────────────────
    prereqs = check_prereqs()

    if not args.api_seulement:
        # ── 1. Services core ──────────────────────────────────────────────
        if prereqs["docker"] and prereqs["docker_compose"]:
            start_docker_core()
            wait_postgres_healthy()
            wait_cassandra_healthy()

            if not args.sans_streaming:
                start_docker_streaming()
        else:
            warn("Docker non disponible — l'API utilisera le mode dégradé (mock data)")

        # ── 2. ETL ────────────────────────────────────────────────────────
        run_etl(skip_download=args.sans_ingestion)

    # ── 3. API & Frontend ─────────────────────────────────────────────────
    if prereqs["npm"]:
        start_frontend()

    start_api()

    # ── 4. Ouverture des onglets et du PPT ───────────────────────────────
    open_pptx()
    time.sleep(1)
    open_browser_tabs()

    # ── 5. Tableau de statut ──────────────────────────────────────────────
    print_status_table()

    # ── 6. Supervision ────────────────────────────────────────────────────
    keep_alive()


if __name__ == "__main__":
    main()
