"""Producteur Kafka – flux temps réel Vélib Métropole (GBFS public, sans clé).

Interroge le flux GBFS station_status toutes les VELIB_POLL_INTERVAL_S secondes
et publie chaque snapshot de station sur le topic VELIB_KAFKA_TOPIC.

Format du message JSON :
{
  "station_id": "12345",
  "num_bikes_available": 5,
  "num_docks_available": 10,
  "is_installed": true,
  "is_renting": true,
  "is_returning": true,
  "last_reported": 1718000000,
  "event_time": "2026-06-13T10:00:00+00:00"
}

Variables d'environnement (voir .env.example) :
  VELIB_GBFS_URL         : URL du feed GBFS (défaut public Smovengo)
  VELIB_POLL_INTERVAL_S  : intervalle en secondes (défaut 30)
  VELIB_KAFKA_TOPIC      : nom du topic Kafka (défaut ude-velib)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [velib_producer] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

GBFS_URL = os.getenv(
    "VELIB_GBFS_URL",
    "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json",
)
POLL_INTERVAL = int(os.getenv("VELIB_POLL_INTERVAL_S", "30"))
TOPIC = os.getenv("VELIB_KAFKA_TOPIC", "ude-velib")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def fetch_stations() -> list[dict]:
    """Fetch the GBFS station_status feed and return the stations list."""
    resp = requests.get(GBFS_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", {}).get("stations", [])


def main() -> None:
    try:
        from kafka import KafkaProducer
    except ImportError:
        logger.error("kafka-python not installed – cannot start Vélib producer")
        sys.exit(1)

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    logger.info("Producteur Vélib démarré · topic=%s · intervalle=%ds", TOPIC, POLL_INTERVAL)

    while True:
        try:
            stations = fetch_stations()
            now = datetime.now(timezone.utc).isoformat()
            for station in stations:
                msg = {
                    "station_id": str(station.get("station_id", "")),
                    "num_bikes_available": station.get("num_bikes_available", 0),
                    "num_docks_available": station.get("num_docks_available", 0),
                    "is_installed": bool(station.get("is_installed", False)),
                    "is_renting": bool(station.get("is_renting", False)),
                    "is_returning": bool(station.get("is_returning", False)),
                    "last_reported": station.get("last_reported"),
                    "event_time": now,
                }
                producer.send(TOPIC, value=msg)
            producer.flush()
            logger.info("Snapshot publié · %d stations · topic=%s", len(stations), TOPIC)
        except requests.RequestException as exc:
            logger.warning("Erreur réseau GBFS : %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.error("Erreur producteur : %s", exc)

        time.sleep(POLL_INTERVAL)


# ── Stubs RATP / Météo (clés API requises – désactivés sans clé) ────────────

def ratp_stub() -> None:
    """Stub producteur RATP – activé uniquement si RATP_API_KEY est défini.

    Clé obtenue sur https://prim.iledefrance-mobilites.fr.
    Sans clé : ne fait rien.
    """
    api_key = os.getenv("RATP_API_KEY", "")
    if not api_key:
        logger.info("RATP_API_KEY absent – producteur RATP désactivé")
        return
    # TODO: implémenter l'appel PRIM IDFM lorsque la clé est disponible
    logger.info("RATP producteur stub – clé présente, implémentation à compléter")


def meteo_stub() -> None:
    """Stub producteur Météo Paris – activé uniquement si OPENWEATHER_API_KEY est défini.

    Clé obtenue sur https://openweathermap.org/api.
    Sans clé : ne fait rien.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        logger.info("OPENWEATHER_API_KEY absent – producteur météo désactivé")
        return
    # TODO: appeler api.openweathermap.org/data/2.5/weather?q=Paris lorsque la clé est présente
    logger.info("Météo producteur stub – clé présente, implémentation à compléter")


if __name__ == "__main__":
    main()
