-- Cassandra schema – C1.2: Base NoSQL pour événements streaming
-- Partitionnement par event_type, tri par event_time DESC pour lectures récentes

CREATE KEYSPACE IF NOT EXISTS ude
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE ude;

CREATE TABLE IF NOT EXISTS events_by_type (
  event_type TEXT,
  event_time TIMESTAMP,
  event_id UUID,
  source_id TEXT,
  arrondissement_code TEXT,
  payload TEXT,
  PRIMARY KEY (event_type, event_time, event_id)
) WITH CLUSTERING ORDER BY (event_time DESC, event_id ASC)
  AND default_time_to_live = 604800;  -- TTL 7 jours

-- C2.2 : Agrégats micro-batch par fenêtre tumbling (query-first)
-- Justification modèle : requête principale = "aggrégats de la fenêtre X pour
-- un event_type donné". La clé de partition window_start distribue la charge
-- par tranche de 10s ; event_type + district_code permettent le filtre en
-- clustering sans ALLOW FILTERING.
CREATE TABLE IF NOT EXISTS events_agg_by_window (
  window_start TIMESTAMP,
  event_type   TEXT,
  district_code TEXT,
  event_count  INT,
  avg_value    DOUBLE,
  PRIMARY KEY (window_start, event_type, district_code)
) WITH CLUSTERING ORDER BY (event_type ASC, district_code ASC)
  AND default_time_to_live = 604800;  -- TTL 7 jours

-- C2.2 : Événements bruts indexés par arrondissement (query-first)
-- Justification modèle : requête principale = "derniers événements du district X".
-- Partition par district_code pour colocaliser les données d'un arrondissement ;
-- tri DESC sur event_time pour retourner les plus récents sans ORDER BY coûteux.
CREATE TABLE IF NOT EXISTS events_by_district (
  district_code TEXT,
  event_time    TIMESTAMP,
  event_id      UUID,
  event_type    TEXT,
  source_id     TEXT,
  payload       TEXT,
  PRIMARY KEY (district_code, event_time, event_id)
) WITH CLUSTERING ORDER BY (event_time DESC, event_id ASC)
  AND default_time_to_live = 604800;  -- TTL 7 jours
