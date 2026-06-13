"""Micro-batch Kafka → Cassandra – C2.2 · fenêtre tumbling 10 secondes.

Consomme le topic 'ude-events', agrège les événements par (event_type, district)
sur des fenêtres fixes de 10 secondes, puis écrit les agrégats dans Cassandra.

Tables Cassandra utilisées (voir cassandra/schema.cql) :
- events_agg_by_window  : agrégats (count, avg_value) par fenêtre + event_type + district
- events_by_district    : événements bruts indexés par arrondissement

Le script se termine proprement (log + sys.exit(0)) si Kafka ou Cassandra
sont inaccessibles, conformément au pattern du producer/consumer existant.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone

TOPIC = "ude-events"
WINDOW_S = 10  # durée de la fenêtre tumbling en secondes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [microbatch] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    # ── Connexion Kafka ──────────────────────────────────────────────────
    try:
        from kafka import KafkaConsumer
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers="kafka:9092",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            group_id="ude-microbatch",
            consumer_timeout_ms=WINDOW_S * 1000,  # sort du for-loop après la fenêtre
        )
        logger.info("Kafka connecté – topic %s", TOPIC)
    except Exception as exc:
        logger.error("Kafka inaccessible – microbatch interrompu : %s", exc)
        sys.exit(0)

    # ── Connexion Cassandra ──────────────────────────────────────────────
    try:
        from cassandra.cluster import Cluster
        cluster = Cluster(["cassandra"], port=9042)
        session = cluster.connect("ude")
        logger.info("Cassandra connectée")
    except Exception as exc:
        logger.error("Cassandra inaccessible – microbatch interrompu : %s", exc)
        consumer.close()
        sys.exit(0)

    # ── Requêtes préparées ───────────────────────────────────────────────
    try:
        insert_agg = session.prepare(
            "INSERT INTO events_agg_by_window "
            "(window_start, event_type, district_code, event_count, avg_value) "
            "VALUES (?, ?, ?, ?, ?)"
        )
        insert_by_district = session.prepare(
            "INSERT INTO events_by_district "
            "(district_code, event_time, event_id, event_type, source_id, payload) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )
    except Exception as exc:
        logger.error("Impossible de préparer les requêtes Cassandra : %s", exc)
        cluster.shutdown()
        consumer.close()
        sys.exit(0)

    logger.info("Micro-batch démarré – fenêtre tumbling %ds", WINDOW_S)

    # ── Boucle principale ────────────────────────────────────────────────
    while True:
        # Alignement du début de fenêtre sur l'epoch (fenêtres reproductibles)
        now_utc = datetime.now(timezone.utc)
        window_epoch = (int(now_utc.timestamp()) // WINDOW_S) * WINDOW_S
        window_start = datetime.fromtimestamp(window_epoch, tz=timezone.utc)

        # Agrégats de la fenêtre : clé = (event_type, district_code)
        aggregates: dict[tuple[str, str], dict] = defaultdict(
            lambda: {"count": 0, "value_sum": 0.0}
        )

        deadline = time.monotonic() + WINDOW_S

        # Consommation des messages de la fenêtre
        try:
            for message in consumer:
                event = message.value
                key = (
                    event.get("event_type", ""),
                    event.get("arrondissement_code", ""),
                )
                agg = aggregates[key]
                agg["count"] += 1
                try:
                    payload_obj = json.loads(event.get("payload", "{}"))
                    agg["value_sum"] += float(payload_obj.get("value", 0))
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

                # Écriture brute dans events_by_district
                try:
                    raw_time_str = event.get("event_time", now_utc.isoformat())
                    event_time = datetime.fromisoformat(raw_time_str.replace("Z", "+00:00"))
                    event_id = uuid.UUID(event.get("event_id", str(uuid.uuid4())))
                    session.execute(insert_by_district, [
                        event.get("arrondissement_code", ""),
                        event_time,
                        event_id,
                        event.get("event_type", ""),
                        event.get("source_id", ""),
                        event.get("payload", "{}"),
                    ])
                except Exception as exc:
                    logger.warning("Échec insert events_by_district : %s", exc)

                if time.monotonic() >= deadline:
                    break
        except StopIteration:
            # consumer_timeout_ms atteint : fin normale de la fenêtre
            pass

        # ── Écriture des agrégats ────────────────────────────────────────
        if aggregates:
            for (evt_type, district), agg in aggregates.items():
                count = agg["count"]
                avg_val = round(agg["value_sum"] / count, 2) if count else 0.0
                try:
                    session.execute(insert_agg, [window_start, evt_type, district, count, avg_val])
                except Exception as exc:
                    logger.warning("Échec insert events_agg_by_window : %s", exc)

            logger.info(
                "Fenêtre %s – %d groupes agrégés (%d événements total)",
                window_start.isoformat(),
                len(aggregates),
                sum(v["count"] for v in aggregates.values()),
            )
        else:
            logger.debug("Fenêtre %s – aucun événement", window_start.isoformat())


if __name__ == "__main__":
    main()
