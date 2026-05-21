from __future__ import annotations
from fastapi import APIRouter
from ..schemas import PipelineRun

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/latest", response_model=PipelineRun | None)
def latest_run():
    """Return the most recent pipeline execution status."""
    try:
        from ..db import pg_fetch_all
        rows = pg_fetch_all(
            """
            SELECT run_date, stage, status, row_count, updated_at
            FROM pipeline_runs
            ORDER BY updated_at DESC
            LIMIT 1
            """
        )
        return PipelineRun(**rows[0]) if rows else None
    except Exception:
        from ..data import latest_pipeline_run
        return PipelineRun(**latest_pipeline_run())
