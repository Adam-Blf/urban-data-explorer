"""Pydantic schemas exposés par l'API."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class ArrondissementKpi(BaseModel):
    code_arrondissement: str
    label: str
    centroid_lon: float | None
    centroid_lat: float | None
    population: int | None
    parc_logements: int | None
    revenu_median: float | None
    prix_m2: float | None
    transactions_an: int | None
    log_sociaux_finances: int | None
    aqi_paris: float | None
    idx_accessibilite: float | None
    idx_tension: float | None
    idx_effort_social: float | None
    idx_attractivite: float | None


class TimelinePoint(BaseModel):
    code_arrondissement: str
    year: int
    month: int
    year_month: str
    prix_m2_median: float | None
    nb_transactions: int | None
    volume_eur: float | None
    prix_m2_median_3m: float | None
    delta_prix_m2_mom: float | None


class IndicatorRow(BaseModel):
    code_arrondissement: str
    label: str
    indicator: str
    value: float | None


class Page[T](BaseModel):
    """Enveloppe de pagination standard."""
    items: list[T]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)
    next_page: int | None = None
    prev_page: int | None = None
