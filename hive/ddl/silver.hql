-- Hive DDL – Silver layer (données nettoyées, normalisées, géocodées)
-- C1.3: Data Lake – couche de transformation

USE ude;

CREATE EXTERNAL TABLE IF NOT EXISTS silver_sources (
  source_id STRING,
  family STRING,
  arrondissement_code STRING,
  latitude DOUBLE,
  longitude DOUBLE,
  code_iris STRING,
  nom_iris STRING,
  address STRING,
  quality_flag STRING
)
PARTITIONED BY (snapshot_date STRING)
STORED AS PARQUET
LOCATION 'hdfs://namenode:8020/data/silver/sources';
