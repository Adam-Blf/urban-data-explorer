@echo off
:: ── Lanceur de soutenance Urban Data Explorer (Windows) ──────────────────
:: Double-cliquer ou lancer depuis PowerShell / cmd
:: Options : --sans-ingestion  --sans-streaming  --api-seulement
:: ─────────────────────────────────────────────────────────────────────────
setlocal

cd /d "%~dp0"

:: Installer les dépendances si absentes
python -c "import fastapi, polars, uvicorn" 2>nul
if %errorlevel% neq 0 (
    echo Installation des dependances Python...
    python -m pip install -r requirements.txt --quiet
)

python lancer_soutenance.py %*
pause
