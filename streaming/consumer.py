"""Consommateur Kafka → Cassandra.

Lit les événements de deux topics :
- 'ude-events'  : événements urbains génériques (producteur existant)
- 'ude-velib'   : snapshots station Vélib (velib_producer.py)

Les Vélib sont sérialisés en JSON dans le champ `payload` de la table
events_by_type avec event_type='velib_snapshot'.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime

from cassandra.cluster import Cluster
from kafka import KafkaConsumer

TOPICS = [
    os.getenv("UDE_KAFKA_TOPIC", "ude-events"),
    os.getenv("VELIB_KAFKA_TOPIC", "ude-velib"),
]
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def _handle_velib(session, insert_stmt, message: dict) -> None:
    """Write a Vélib station snapshot as a generic event row."""
    session.execute(insert_stmt, [
        "velib_snapshot",
        datetime.fromisoformat(message["event_time"]),
        uuid.uuid4(),
        "velib-gbfs",
        None,  # arrondissement_code – non disponible depuis station_id seul
        json.dumps({
            "station_id": message.get("station_id"),
            "bikes": message.get("num_bikes_available"),
            "docks": message.get("num_docks_available"),
        }),
    ])


def _handle_generic(session, insert_stmt, message: dict) -> None:
    """Write a generic urban event row."""
    session.execute(insert_stmt, [
        message["event_type"],
        datetime.fromisoformat(message["event_time"]),
        uuid.UUID(message["event_id"]),
        message["source_id"],
        message["arrondissement_code"],
        message["payload"],
    ])


def main():
    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="ude-consumer",
    )

    cluster = Cluster([os.getenv("CASSANDRA_HOST", "cassandra")],
                      port=int(os.getenv("CASSANDRA_PORT", "9042")))
    session = cluster.connect(os.getenv("CASSANDRA_KEYSPACE", "ude"))

    insert = session.prepare(
        "INSERT INTO events_by_type (event_type, event_time, event_id, source_id, arrondissement_code, payload) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )

    print(f"Consommateur Kafka démarré – topics: {TOPICS}")

    velib_topic = os.getenv("VELIB_KAFKA_TOPIC", "ude-velib")

    for message in consumer:
        event = message.value
        try:
            if message.topic == velib_topic:
                _handle_velib(session, insert, event)
                print(f"← velib | station {event.get('station_id')}")
            else:
                _handle_generic(session, insert, event)
                print(f"← {event['event_type']} | {event.get('arrondissement_code')}")
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] message ignoré : {exc}")


if __name__ == "__main__":
    main()
