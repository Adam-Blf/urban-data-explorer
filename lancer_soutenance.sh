#!/usr/bin/env bash
# ── Lanceur de soutenance Urban Data Explorer ─────────────────────────────
# Usage : ./lancer_soutenance.sh [options]
#   --sans-ingestion   Ne pas retélécharger les sources
#   --sans-streaming   Ne pas démarrer Kafka/Zookeeper
#   --api-seulement    Docker déjà lancé, juste API + front
# ──────────────────────────────────────────────────────────────────────────
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Chercher python3.11+ ou python3 ou python
PYTHON=""
for cmd in python3.11 python3.12 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(sys.version_info >= (3,11))" 2>/dev/null || echo "False")
        if [ "$VER" = "True" ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌  Python 3.11+ requis. Installez-le puis relancez."
    exit 1
fi

# Installer les dépendances si nécessaire (première fois)
if ! "$PYTHON" -c "import fastapi, polars, uvicorn" 2>/dev/null; then
    echo "📦  Installation des dépendances Python..."
    "$PYTHON" -m pip install -r requirements.txt --quiet
fi

exec "$PYTHON" lancer_soutenance.py "$@"
