# Schémas data

Diagrammes Mermaid · GitHub les rend nativement dans la preview Markdown.

## 1. Pipeline médaillon · vue d'ensemble

```mermaid
flowchart LR
    subgraph Sources["Sources ouvertes"]
        S1[data.gouv DVF]
        S2[OpenData Paris<br/>10 datasets]
        S3[INSEE Filosofi]
        S4[Airparif]
        S5[data.gouv POI<br/>musées · hôpitaux · monuments]
    end

    subgraph Bronze["Bronze · /raw"]
        B[Parquet partitionné<br/>year=YYYY/month=MM/day=DD]
    end

    subgraph Silver["Silver · /silver"]
        SL[Polars · Shapely<br/>cleaning + 6 règles<br/>jointure spatiale<br/>window functions]
    end

    subgraph Gold["Gold · /gold/urban.duckdb"]
        G1[dim_arrondissement]
        G2[dim_poi]
        G3[fact_transactions_arr_mois]
        G4[fact_logements_sociaux]
        G5[fact_revenus_arr]
        G6[fact_air_quality]
        G7[fact_poi_arr]
        K[kpi_arrondissement<br/>4 indicateurs composites]
        T[timeline_arrondissement]
    end

    subgraph Serving["Couche serving"]
        API[FastAPI<br/>JWT + pagination]
        FE[Frontend MapLibre<br/>+ Chart.js]
    end

    Sources --> B
    B --> SL
    SL --> G1 & G2 & G3 & G4 & G5 & G6 & G7
    G3 --> K
    G4 --> K
    G5 --> K
    G6 --> K
    G7 --> K
    G3 --> T
    K --> API
    T --> API
    G2 --> API
    API --> FE
```

## 2. Modèle relationnel Gold

```mermaid
erDiagram
    dim_arrondissement ||--o{ fact_transactions_arr_mois : "code_arrondissement"
    dim_arrondissement ||--o{ fact_logements_sociaux     : "code_arrondissement"
    dim_arrondissement ||--o{ fact_revenus_arr           : "code_arrondissement"
    dim_arrondissement ||--o{ fact_poi_arr               : "code_arrondissement"
    dim_arrondissement ||--o{ dim_poi                    : "code_arrondissement"
    dim_arrondissement ||--|| kpi_arrondissement         : "code_arrondissement"
    fact_transactions_arr_mois ||--o{ timeline_arrondissement : "(arr, year, month)"

    dim_arrondissement {
        VARCHAR  code_arrondissement PK
        VARCHAR  label
        DOUBLE   centroid_lon
        DOUBLE   centroid_lat
        DOUBLE   area_km2
    }
    dim_poi {
        VARCHAR  code_arrondissement FK
        VARCHAR  category
        VARCHAR  subcategory
        VARCHAR  name
        DOUBLE   lon
        DOUBLE   lat
    }
    fact_transactions_arr_mois {
        VARCHAR  code_arrondissement FK
        INTEGER  year
        INTEGER  month
        INTEGER  nb_transactions
        DOUBLE   prix_m2_median
        DOUBLE   prix_m2_moyen
        DOUBLE   volume_eur
    }
    fact_logements_sociaux {
        VARCHAR  code_arrondissement FK
        INTEGER  year
        INTEGER  nb_logements_finances
    }
    fact_revenus_arr {
        VARCHAR  code_arrondissement FK
        DOUBLE   MED21
        DOUBLE   PIMP21
        DOUBLE   TP6021
    }
    fact_poi_arr {
        VARCHAR  code_arrondissement FK
        VARCHAR  category
        VARCHAR  subcategory
        BIGINT   nb_poi
    }
    kpi_arrondissement {
        VARCHAR  code_arrondissement PK
        VARCHAR  label
        DOUBLE   prix_m2
        INTEGER  population
        INTEGER  parc_logements
        DOUBLE   revenu_median
        DOUBLE   idx_accessibilite
        DOUBLE   idx_tension
        DOUBLE   idx_effort_social
        DOUBLE   idx_attractivite
    }
    timeline_arrondissement {
        VARCHAR  code_arrondissement FK
        INTEGER  year
        INTEGER  month
        VARCHAR  year_month
        DOUBLE   prix_m2_median
        DOUBLE   prix_m2_median_3m
        DOUBLE   delta_prix_m2_mom
    }
```

## 3. Flux d'authentification API

```mermaid
sequenceDiagram
    participant U as Utilisateur (frontend)
    participant API as FastAPI
    participant DB as DuckDB (gold)

    U->>API: POST /auth/login {username, password}
    API->>API: verify_credentials()
    API-->>U: 200 {access_token: JWT}

    U->>API: GET /datamarts/arrondissements?...<br/>Authorization: Bearer JWT
    API->>API: get_current_user() · jwt.decode()
    API->>DB: SELECT * FROM kpi_arrondissement WHERE ... LIMIT N OFFSET M
    DB-->>API: rows
    API-->>U: 200 Page[ArrondissementKpi]
```

## 4. Partitionnement Bronze/Silver

```mermaid
graph TD
    R["raw/"] --> Sdvf[dvf/]
    R --> Sarr[arrondissements/]
    R --> Sfilo[filosofi/]
    R --> Spoi[velib_stations/<br/>belib_bornes/<br/>ecoles_elementaires/<br/>...etc]

    Sdvf --> Y1["year=2024/"]
    Y1 --> M1["month=05/"]
    M1 --> D1["day=03/dvf.parquet"]

    Sarr --> Y2["year=2024/"]
    Y2 --> M2["month=05/"]
    M2 --> D2["day=03/arrondissements.geojson"]
```
