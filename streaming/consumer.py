"""Consommateur Kafka → Cassandra.

Lit les événements du topic 'ude-events' et les persiste dans Cassandra
pour alimenter le flux temps réel du dashboard.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from cassandra.cluster import Cluster
from kafka import KafkaConsumer

TOPIC = "ude-events"


def main():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers="kafka:9092",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="ude-consumer",
    )

    cluster = Cluster(["cassandra"], port=9042)
    session = cluster.connect("ude")

    insert = session.prepare(
        "INSERT INTO events_by_type (event_type, event_time, event_id, source_id, arrondissement_code, payload) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )

    print("Consommateur Kafka démarré – écriture Cassandra")

    for message in consumer:
        event = message.value
        session.execute(insert, [
            event["event_type"],
            datetime.fromisoformat(event["event_time"]),
            uuid.UUID(event["event_id"]),
            event["source_id"],
            event["arrondissement_code"],
            event["payload"],
        ])
        print(f"← {event['event_type']} | {event['arrondissement_code']}")


if __name__ == "__main__":
    main()
