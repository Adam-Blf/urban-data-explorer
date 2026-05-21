from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter
from ..schemas import RepoBadge, RepoScanSummary

router = APIRouter(prefix="/repo", tags=["repo"])
ROOT = Path(__file__).resolve().parents[2]


def _badge(badge_id: str, label: str, group: str, path: str, note: str, required: bool = True) -> RepoBadge:
    present = (ROOT / path).exists()
    return RepoBadge(
        badge_id=badge_id, label=label, group=group, path=path,
        present=present, required=required,
        note=note if present else f"Manquant: {note}",
    )


@router.get("/scan", response_model=RepoScanSummary)
def scan_repo():
    badges = [
        _badge("docs", "Documentation", "Base", "README.md", "README prêt"),
        _badge("compose", "Orchestration", "Base", "docker-compose.yml", "Stack Docker"),
        _badge("env", "Variables", "Base", ".env.example", "Variables d'env"),
        _badge("start-app", "Démarrage", "Run", "scripts/start_app.ps1", "Script lancement"),
        _badge("start-full", "Stack complète", "Run", "scripts/start_full.ps1", "Script lake+streaming"),
        _badge("catalog", "Catalogue", "Code", "etl/catalog.py", "Sources centralisées"),
        _badge("etl", "ETL Polars", "Code", "etl/processing.py", "Bronze/Silver/Gold"),
        _badge("api", "API FastAPI", "Code", "api/main.py", "Point d'entrée API"),
        _badge("frontend", "Frontend React", "Code", "frontend/src/App.tsx", "Dashboard interactif"),
        _badge("postgres", "PostgreSQL", "Storage", "postgres/init.sql", "Schéma relationnel"),
        _badge("cassandra", "Cassandra", "Storage", "cassandra/schema.cql", "Schéma NoSQL"),
        _badge("hive-bronze", "Hive Bronze", "Storage", "hive/ddl/bronze.hql", "DDL Bronze"),
        _badge("hive-silver", "Hive Silver", "Storage", "hive/ddl/silver.hql", "DDL Silver"),
        _badge("hive-gold", "Hive Gold", "Storage", "hive/ddl/gold.hql", "DDL Gold"),
        _badge("datasets", "Datasets", "Data", "data/raw/downloads", "Données locales", False),
        _badge("report", "Rapport PDF", "Delivery", "scripts/generate_report_pdf.py", "Générateur", False),
    ]
    present = sum(1 for b in badges if b.present)
    return RepoScanSummary(
        generated_at=datetime.now(timezone.utc),
        total=len(badges), present=present, missing=len(badges) - present,
        badges=badges,
    )
