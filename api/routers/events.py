from __future__ import annotations
import json
from fastapi import APIRouter
from ..schemas import EventRow

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/recent", response_model=list[EventRow])
def recent_events(limit: int = 50, event_type: str = "service_snapshot"):
    """Return the latest streaming events stored in Cassandra."""
    try:
        from ..db import cassandra_session
        session = cassandra_session()
        query = """
            SELECT event_id, event_type, source_id, arrondissement_code, payload, event_time
            FROM events_by_type
            WHERE event_type = %s
            LIMIT %s
        """
        rows = session.execute(query, [event_type, limit])
        result = [
            EventRow(
                event_id=str(row.event_id),
                event_type=row.event_type,
                source_id=str(row.source_id),
                district_code=row.arrondissement_code,
                payload=json.loads(row.payload),
                event_time=row.event_time,
            )
            for row in rows
        ]
        session.cluster.shutdown()
        return result
    except Exception:
        from ..data import recent_events as mock_events
        events = mock_events()
        # Respecter les paramètres de filtre et de limite dans le mode fallback
        filtered = [e for e in events if e.get("event_type") == event_type]
        return [EventRow(**e) for e in filtered[:limit]]
