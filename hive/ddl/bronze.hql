-- Hive DDL – Bronze layer (données brutes)
-- C1.3: Data Lake – couche d'ingestion

CREATE DATABASE IF NOT EXISTS ude;
USE ude;

CREATE EXTERNAL TABLE IF NOT EXISTS bronze_sources (
  source_id STRING,
  raw_json STRING,
  ingest_time TIMESTAMP
)
PARTITIONED BY (snapshot_date STRING, source STRING)
STORED AS PARQUET
LOCATION 'hdfs://namenode:8020/data/bronze/sources';
