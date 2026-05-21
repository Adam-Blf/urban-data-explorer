"""Pydantic schemas pour l'API Urban Data Explorer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SourceRow(BaseModel):
    source_id: str
    title: str
    provider: str
    family: str
    catalog_url: str
    metadata_only: bool = False


class DistrictRow(BaseModel):
    code: str
    name: str
    label: str
    x: int = 0
    y: int = 0
    family_counts: dict[str, int]
    accessibility_index: int
    pressure_index: int
    attractiveness_index: int
    score: int
    immobilier_idx: int = 0
    logement_social_idx: int = 0
    revenu_idx: int = 0
    cadre_vie_idx: int = 0
    environnement_idx: int = 0
    prix_m2: float = 0.0
    logements_sociaux_count: int = 0
    logement_social_pct: float = 0.0
    revenu_median: float = 0.0
    sales_volume: int = 0


class Overview(BaseModel):
    source_count: int
    family_count: int
    district_count: int
    accessibility_index: int
    pressure_index: int
    attractiveness_index: int
    source_family_counts: dict[str, int] = {}
    immobilier_idx: int = 0
    logement_social_idx: int = 0
    revenu_idx: int = 0
    cadre_vie_idx: int = 0
    environnement_idx: int = 0
    prix_m2: float = 0.0
    logement_social_pct: float = 0.0
    revenu_median: float = 0.0


class TimelinePoint(BaseModel):
    month: str
    label: str
    activity: int
    accessibility_index: float
    pressure_index: float
    attractiveness_index: float
    immobilier_idx: float = 0.0
    logement_social_idx: float = 0.0
    revenu_idx: float = 0.0
    cadre_vie_idx: float = 0.0
    environnement_idx: float = 0.0


class EventRow(BaseModel):
    event_id: str
    event_type: str
    source_id: str
    district_code: str | None = None
    payload: dict[str, Any] = {}
    event_time: datetime


class PipelineRun(BaseModel):
    run_date: str
    stage: str
    status: str
    row_count: int
    updated_at: datetime | None = None
    summary: str = ""


class RepoBadge(BaseModel):
    badge_id: str
    label: str
    group: str
    path: str
    present: bool
    required: bool = True
    note: str = ""


class RepoScanSummary(BaseModel):
    generated_at: datetime
    total: int
    present: int
    missing: int
    badges: list[RepoBadge]
