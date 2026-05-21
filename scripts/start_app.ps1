# Lancement local - API + Frontend (sans Docker)

Write-Host "  Urban Data Explorer - Demarrage local" -ForegroundColor Cyan

# Verifier Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "  [ERROR] Python non trouve" -ForegroundColor Red
    exit 1
}

# Installer les dependances Python
Write-Host "  -> Installation dependances Python..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Lancer l'API en arriere-plan
Write-Host "  -> Lancement API (port 8000)..." -ForegroundColor Yellow
$api = Start-Process python -ArgumentList "-m", "uvicorn", "api.main:app", "--port", "8000", "--host", "127.0.0.1" -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 3

# Verifier que l'API repond
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
    Write-Host "  -> API status: $($health.status) - $($health.sources) sources, $($health.districts) arrondissements" -ForegroundColor Green
} catch {
    Write-Host "  [WARN] API pas encore prete" -ForegroundColor Yellow
}

# Lancer le frontend
if (Test-Path "frontend/node_modules") {
    Write-Host "  -> Lancement Frontend (port 5173)..." -ForegroundColor Yellow
    $frontend = Start-Process cmd.exe -ArgumentList "/c", "npm", "run", "dev" -WorkingDirectory "frontend" -PassThru -WindowStyle Minimized
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:5173"
} else {
    Write-Host "  -> Installation + lancement Frontend..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    $frontend = Start-Process cmd.exe -ArgumentList "/c", "npm", "run", "dev" -PassThru -WindowStyle Minimized
    Set-Location ..
    Start-Sleep -Seconds 5
    Start-Process "http://localhost:5173"
}

Write-Host "  -> Projet lance avec succes !" -ForegroundColor Green
Write-Host "    API:       http://localhost:8000/docs"
Write-Host "    Frontend:  http://localhost:5173"
Write-Host "    Ctrl+C pour arreter"

# Attendre
Wait-Process -Id $api.Id
