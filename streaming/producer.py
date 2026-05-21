"""Producteur Kafka – simule des événements urbains pour Paris.

Envoie des événements JSON sur le topic 'ude-events' toutes les 2 secondes,
simulant l'activité temps réel des capteurs urbains parisiens.
"""

from __future__ import annotations

import json
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer

TOPIC = "ude-events"
DISTRICTS = [f"750{i:02d}" for i in range(1, 21)]
FAMILIES = ["green_space", "mobility", "public_service", "education", "culture", "health", "housing", "pressure"]
EVENT_TYPES = ["service_snapshot", "sensor_update", "ingest_complete"]


def create_event() -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": random.choice(EVENT_TYPES),
        "source_id": f"src-{random.randint(1, 19):03d}",
        "arrondissement_code": random.choice(DISTRICTS),
        "payload": json.dumps({
            "family": random.choice(FAMILIES),
            "value": round(random.uniform(10, 95), 1),
            "message": "Mise à jour capteur urbain Paris",
        }),
        "event_time": datetime.now(timezone.utc).isoformat(),
    }


def main():
    producer = KafkaProducer(
        bootstrap_servers="kafka:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    print("Producteur Kafka démarré – topic:", TOPIC)

    while True:
        event = create_event()
        producer.send(TOPIC, value=event)
        print(f"→ {event['event_type']} | {event['arrondissement_code']}")
        time.sleep(2)


if __name__ == "__main__":
    main()
