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
