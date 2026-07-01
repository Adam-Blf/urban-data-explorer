# Guide jury - Urban Data Explorer

**Observatoire socio-urbain Paris** : 82 sources Open Data, 20 arrondissements, 5 indices,
architecture medaillon Bronze/Silver/Gold, API FastAPI, streaming Kafka/Cassandra.

Pour chaque competence du referentiel, le tableau indique OU dans le code citer.

---

## C1 - Architecture des donnees

### C1.1 - Catalogue de sources (82 sources, 4 familles)

| Element | Fichier | Ligne | Symbole |
|---------|---------|-------|---------|
| Dataclass SourceSpec | `etl/bronze/catalog.py` | 27 | `SourceSpec` |
| Liste ALL_SOURCES (82 entrees) | `etl/bronze/catalog.py` | 59 | `ALL_SOURCES` |
| Famille mobilite (17 sources) | `etl/bronze/catalog.py` | 64 | `velib_stations` → `ascenseurs_osm` |
| Famille vie_quotidienne (42 sources) | `etl/bronze/catalog.py` | 248 | `maternelles` → `librairies_papeteries` |
| Famille environnement (11 sources) | `etl/bronze/catalog.py` | 750 | `espaces_verts` → `stations_velo_osm` |
| Famille logement_urbanisme (12 sources) | `etl/bronze/catalog.py` | 879 | `logements_sociaux` → `risque_radon` |
| INDEX source_id → SourceSpec | `etl/bronze/catalog.py` | 1018 | `SOURCE_MAP` |
| Dictionnaire FAMILIES | `etl/bronze/catalog.py` | 1020 | `FAMILIES` |
| Sources Overpass API (requetes Overpass) | `etl/bronze/catalog.py` | 175 | `parkings_velos.download_url` |

### C1.2 - Architecture medaillon Bronze / Silver / Gold

| Couche | Fichier | Ligne | Description |
|--------|---------|-------|-------------|
| Bronze : ecriture Parquet brut | `spark/jobs/batch_ingest.py` | 19 | `BRONZE_DIR = data/bronze/` |
| Bronze : lecture CSV → Polars | `etl/bronze/io.py` | 16 | `load_source_as_silver()` |
| Silver : normalisation et geocodage | `etl/silver/processing.py` | 260 | `build_silver_record()` |
| Silver : ecriture Parquet normalise | `spark/jobs/batch_ingest.py` | 20 | `SILVER_DIR = data/silver/` |
| Gold : datamart dashboard | `etl/silver/processing.py` | 383 | `build_gold_dashboard()` |
| Gold : datamart timeline | `etl/silver/processing.py` | 465 | `build_gold_timeline()` |
| Gold : ecriture + push PostgreSQL | `spark/jobs/build_gold.py` | 48 | `main()` |
| Orchestration batch ingest complet | `spark/jobs/batch_ingest.py` | 23 | `main()` |

---

## C2 - Pipeline ETL et transformation

### C2.1 - Authentification et quotas (securite API)

| Element | Fichier | Ligne | Description |
|---------|---------|-------|-------------|
| Configuration JWT | `api/security.py` | 30 | `JWT_SECRET`, `TOKEN_TTL_MIN` |
| Configuration quotas | `api/security.py` | 34 | `QUOTA_ANON=120`, `QUOTA_AUTH=600` |
| Hash PBKDF2-HMAC-SHA256 | `api/security.py` | 52 | `hash_password()` |
| Verification mot de passe | `api/security.py` | 57 | `verify_password()` |
| Creation jeton JWT | `api/security.py` | 84 | `create_access_token()` |
| Decodage/validation JWT | `api/security.py` | 91 | `decode_token()` |
| Dependance FastAPI : user courant | `api/security.py` | 103 | `get_current_user()` |
| Limitation debit par IP (sliding window) | `api/security.py` | 125 | `check_quota()` |
| Montage quota sur toutes les routes | `api/main.py` | 37 | `dependencies=[Depends(check_quota)]` |
| Route POST /auth/token | `api/routers/auth.py` | 20 | `login()` |
| Route GET /auth/me (admin requis) | `api/routers/auth.py` | 28 | `me()` |

### C2.2 - Streaming Kafka/Cassandra

| Element | Fichier | Ligne | Description |
|---------|---------|-------|-------------|
| Producteur urbain (evenements JSON) | `streaming/producer.py` | 23 | `create_event()` |
| Boucle producteur 2s | `streaming/producer.py` | 38 | `main()` |
| Producteur Velib (GBFS temps reel) | `streaming/velib_producer.py` | 50 | `fetch_stations()` |
| Consommateur dual-topic | `streaming/consumer.py` | 56 | `main()` |
| Handler evenement velib_snapshot | `streaming/consumer.py` | 28 | `_handle_velib()` |
| Handler evenement urbain generique | `streaming/consumer.py` | 44 | `_handle_generic()` |
| Micro-batch fenetre tumbling 10s | `streaming/microbatch.py` | 24 | `WINDOW_S = 10` |
| Agregation par (event_type, district) | `streaming/microbatch.py` | 87 | `aggregates` dict |
| Ecriture agregats dans Cassandra | `streaming/microbatch.py` | 132 | boucle `for (evt_type, district)` |

### C2.3 - Transformation et geocodage

| Element | Fichier | Ligne | Description |
|---------|---------|-------|-------------|
| Parsing colonnes geo_point | `etl/silver/processing.py` | 34 | `_parse_geo_point()` |
| Normalisation codes arrondissement | `etl/silver/processing.py` | 73 | `_normalize_code()` |
| Point-in-polygon (ray-casting) | `etl/silver/processing.py` | 159 | `_point_in_polygon()` |
| Geocodage IRIS offline | `etl/silver/processing.py` | 199 | `resolve_iris()` |
| Fallback API adresse.data.gouv.fr | `etl/silver/processing.py` | 248 | `reverse_geocode_api()` |
| Construction record Silver complet | `etl/silver/processing.py` | 260 | `build_silver_record()` |
| Telechargement HTTP des CSV | `etl/bronze/scraper.py` | 14 | `download_dataset()` |
| Extraction metadonnees Opendatasoft | `etl/bronze/scraper.py` | 44 | `scrape_catalog_metadata()` |

### C2.4 - Metriques de pipeline et optimisation

| Element | Fichier | Ligne | Description |
|---------|---------|-------|-------------|
| Enregistrement metriques par etape | `etl/gold/metrics.py` | 22 | `record_stage()` |
| Persistance Parquet append | `etl/gold/metrics.py` | 56 | `METRICS_PATH` |
| Lecture metriques historiques | `etl/gold/metrics.py` | 87 | `load_metrics()` |
| Exposition via API | `api/routers/pipeline.py` | 22 | `pipeline_metrics()` |
| Rapport qualite Gold (completeness, out-of-range) | `etl/silver/quality.py` | 68 | `compute_quality()` |
| Regles de plages numeriques attendues | `etl/silver/quality.py` | 26 | `RANGE_RULES` |
| Exposition via API | `api/routers/pipeline.py` | 33 | `pipeline_quality()` |

---

## C3 - Calcul des 5 indices (formules)

Toutes les formules se trouvent dans `api/data.py` (priorite ETL) et `etl/silver/processing.py` (calcul Polars).

| Indice | Fichier | Ligne | Formule |
|--------|---------|-------|---------|
| `immobilier_idx` (prix DVF) | `api/data.py` | 125 | `(prix_m2 - 8000) / (16000 - 8000) * 100`, clamp 10-95 |
| `logement_social_idx` (% HLM) | `api/data.py` | 126 | `logement_social_pct * 2.5`, clamp 5-95 |
| `revenu_idx` (Filosofi) | `api/data.py` | 127 | `(revenu_median - 20000) / (48000 - 20000) * 100`, clamp 10-95 |
| `cadre_vie_idx` (services + env) | `api/data.py` | 135 | si counts ETL : `20 + (vq_norm*0.55 + env_norm*0.45) * 65` ; sinon proxy eco |
| `environnement_idx` (espaces verts) | `api/data.py` | 150 | si count ETL : `env * 7.5` ; sinon proxy abordabilite |
| `accessibilite_idx` (m2/revenu) | `api/data.py` | 162 | `(revenu_median / prix_m2) / 4.0 * 100` |
| Score global | `api/data.py` | 166 | moyenne des 5 indices |
| Valeurs de reference (fallback) | `etl/silver/processing.py` | 347 | `PRIX_M2_BASES`, `REVENU_MEDIAN_BASES`, etc. |
| Sources reelles DVF 2023 | `etl/bronze/external.py` | 59 | `load_dvf_prices()` → mediane prix/m2 par arr. |
| Sources reelles INSEE Filosofi | `etl/bronze/external.py` | 100 | `load_filosofi_income()` → revenu median IRIS |

---

## C4 - API FastAPI et base de donnees

### C4.1 - Structure API et Schemas Pydantic

| Element | Fichier | Ligne | Description |
|---------|---------|-------|-------------|
| Creation app FastAPI | `api/main.py` | 30 | `app = FastAPI(...)` |
| Schema DistrictRow | `api/schemas.py` | 21 | `class DistrictRow(BaseModel)` |
| Schema Overview | `api/schemas.py` | 46 | `class Overview(BaseModel)` |
| Schema TimelinePoint | `api/schemas.py` | 64 | `class TimelinePoint(BaseModel)` |
| Schema EventRow | `api/schemas.py` | 78 | `class EventRow(BaseModel)` |
| Schema PipelineRun | `api/schemas.py` | 87 | `class PipelineRun(BaseModel)` |

### C4.2 - Routes datamarts (filtrable)

| Element | Fichier | Ligne | Description |
|---------|---------|-------|-------------|
| GET /datamarts/dashboard | `api/routers/datamarts.py` | 24 | `dashboard()` - filtres + tri |
| GET /datamarts/overview | `api/routers/datamarts.py` | 41 | `overview()` - KPIs globaux |
| GET /datamarts/timeline | `api/routers/datamarts.py` | 46 | `timeline()` - 12 mois |
| GET /datamarts/geojson/{level} | `api/routers/datamarts.py` | 50 | `get_geojson()` - niveaux 0-4 |
| GET /catalog/sources | `api/routers/catalog.py` | 9 | `sources()` - filtre par famille |
| GET /pipeline/latest | `api/routers/pipeline.py` | 10 | `latest_run()` |

### C4.3 - Bases de donnees (PostgreSQL + Cassandra)

| Element | Fichier | Ligne | Description |
|---------|---------|-------|-------------|
| Connexion PostgreSQL (psycopg2) | `api/db.py` | 17 | `pg_conn()` context manager |
| Requete read PostgreSQL | `api/db.py` | 32 | `pg_fetch_all()` |
| Requete write PostgreSQL | `api/db.py` | 40 | `pg_execute()` |
| Connexion Cassandra (lazy singleton) | `api/db.py` | 52 | `cassandra_session()` |
| COPY bulk vers PostgreSQL | `spark/jobs/build_gold.py` | 27 | `_write_pg()` |
| Strategie 3 couches (PG/Parquet/math) | `api/data.py` | 200 | `district_rows()` |

### C4.4 - Observabilite (Prometheus)

| Element | Fichier | Ligne | Description |
|---------|---------|-------|-------------|
| Compteur requetes HTTP | `api/observability.py` | 24 | `REQUEST_COUNT` |
| Histogramme latences | `api/observability.py` | 29 | `REQUEST_LATENCY` |
| Middleware instrumentation | `api/observability.py` | 38 | `prometheus_middleware()` |
| Endpoint /metrics | `api/observability.py` | 59 | `metrics_endpoint()` |

---

## C5 - Recherche semantique

| Element | Fichier | Ligne | Description |
|---------|---------|-------|-------------|
| Descriptions textuelles des 20 arrondissements | `api/search.py` | 29 | `DISTRICT_DESCRIPTIONS` |
| Projection TF-IDF (hashing trick 64 dims) | `api/search.py` | 71 | `_to_vector()` |
| Similarite cosinus (dot product L2-norme) | `api/search.py` | 82 | `_cosine()` |
| Vecteurs pre-calcules a l'import | `api/search.py` | 89 | `_DISTRICT_VECTORS` |
| Recherche en memoire | `api/search.py` | 97 | `semantic_search_memory()` |
| Seedage pgvector PostgreSQL | `api/search.py` | 123 | `seed_postgres()` |
| Recherche pgvector (operateur <=>) | `api/search.py` | 149 | `semantic_search_pg()` |
| Dispatcher (pgvector → fallback memoire) | `api/search.py` | 182 | `semantic_search()` |

---

## C6 - Resilience et qualite des donnees

| Mecanisme | Fichier | Ligne | Description |
|-----------|---------|-------|-------------|
| Fallback 3 couches (PG/Parquet/math) | `api/data.py` | 200 | `district_rows()` |
| Fallback geocodage (IRIS → API → none) | `etl/silver/processing.py` | 280 | `build_silver_record()` |
| Cache LRU geocodage API | `etl/silver/processing.py` | 223 | `_reverse_geocode_cached()` |
| Cache LRU GeoJSON | `api/data.py` | 560 | `_load_geojson()` |
| Cache LRU district_rows | `api/data.py` | 200 | `@lru_cache(maxsize=1)` |
| Metriques ne bloquent jamais le pipeline | `etl/gold/metrics.py` | 81 | `except Exception: print([WARN])` |
| Rapport qualite completeness + out-of-range | `etl/silver/quality.py` | 68 | `compute_quality()` |
| Microbatch : arret propre si Kafka/Cassandra KO | `streaming/microbatch.py` | 43 | `sys.exit(0)` sur exception |

---

## Repertoire des fichiers par couche

```
etl/
  catalog.py          82 sources, 4 familles, SourceSpec dataclass
  scraper.py          telechargement HTTP, metadonnees Opendatasoft
  io.py               CSV/TSV/GZ → Silver DataFrame (Polars)
  processing.py       Bronze → Silver (geocodage, normalisation) + Gold (datamarts)
  external.py         DVF 2023 (prix m2) + INSEE Filosofi 2020 (revenus)
  metrics.py          metriques ETL par etape (append Parquet)
  quality.py          rapport qualite datasets Gold

api/
  main.py             entrypoint FastAPI (CORS, quotas, routers)
  data.py             donnees local-first (5 indices, 3 fallbacks)
  db.py               connexions PostgreSQL + Cassandra
  security.py         JWT, PBKDF2, quotas par IP
  schemas.py          modeles Pydantic
  observability.py    Prometheus (counter + histogram)
  search.py           TF-IDF hashing + pgvector
  routers/
    auth.py           POST /auth/token, GET /auth/me
    catalog.py        GET /catalog/sources
    datamarts.py      GET /datamarts/dashboard|overview|timeline|geojson
    pipeline.py       GET /pipeline/latest|metrics|quality
    events.py         GET /events/recent (Cassandra → fallback)
    health.py         GET /health

spark/jobs/
  batch_ingest.py     orchestration Bronze + Silver (Polars)
  build_gold.py       construction datamarts Gold + push PostgreSQL

streaming/
  producer.py         evenements urbains → Kafka (ude-events)
  velib_producer.py   Velib GBFS → Kafka (ude-velib)
  consumer.py         Kafka (dual-topic) → Cassandra
  microbatch.py       agregation fenetre tumbling 10s → Cassandra
```
