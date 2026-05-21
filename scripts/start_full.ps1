# Lancement complet avec Docker (lake + streaming + core)

Write-Host "`n  Urban Data Explorer – Stack complète Docker`n" -ForegroundColor Cyan

docker compose up -d postgres cassandra api frontend
Start-Sleep -Seconds 5

# Init Cassandra
function Invoke-WithRetry {
    param([string]$Desc, [scriptblock]$Action, [int]$Attempts = 12, [int]$Delay = 10)
    for ($i = 1; $i -le $Attempts; $i++) {
        & $Action
        if ($LASTEXITCODE -eq 0) { return }
        if ($i -lt $Attempts) { Start-Sleep -Seconds $Delay }
    }
    throw "Échec: $Desc après $Attempts tentatives."
}

Invoke-WithRetry -Desc "Cassandra init" -Action { docker compose exec -T cassandra bash -lc "cqlsh -f /scripts/../cassandra/schema.cql" }

Write-Host "`n  ✓ Stack lancée !" -ForegroundColor Green
Start-Process "http://localhost:8080"
Start-Process "http://localhost:8000/docs"
