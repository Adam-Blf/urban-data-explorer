-- Hive DDL – Gold layer (datamarts agrégés pour le dashboard)
-- C1.3: Data Lake – couche de valorisation

USE ude;

CREATE EXTERNAL TABLE IF NOT EXISTS gold_dashboard (
  arrondissement_code STRING,
  green_space_count INT,
  mobility_count INT,
  public_service_count INT,
  education_count INT,
  culture_count INT,
  health_count INT,
  housing_count INT,
  pressure_count INT,
  accessibility_index DOUBLE,
  pressure_index DOUBLE,
  attractiveness_index DOUBLE
)
STORED AS PARQUET
LOCATION 'hdfs://namenode:8020/data/gold/dashboard';

CREATE EXTERNAL TABLE IF NOT EXISTS gold_timeline (
  arrondissement_code STRING,
  year INT,
  month INT,
  record_count INT,
  accessibility_index DOUBLE,
  pressure_index DOUBLE,
  attractiveness_index DOUBLE
)
STORED AS PARQUET
LOCATION 'hdfs://namenode:8020/data/gold/timeline';
