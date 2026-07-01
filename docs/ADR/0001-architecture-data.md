# ADR 0001 · Architecture de données Urban Data Explorer

Date : 2026-06 · Statut : accepté · Binôme : Adam Beloucif & Émilien Morice

## Contexte

Projet RNCP40875 Bloc 1 : construire une architecture complète de stockage et de
traitement de données, sur le thème du logement à Paris, avec restitution
cartographique. L'évaluation couvre C1.1 à C2.4.

## Décisions

### 1. Pattern médaillon Bronze / Silver / Gold (C1.3)
Stockage par zones en Parquet (colonnaire, compressé). Bronze = brut, Silver =
normalisé + géocodé, Gold = datamarts analytiques. **Pourquoi** : séparation des
responsabilités, rejouabilité, performance de lecture.

### 2. Polars plutôt que Pandas/Spark local (C2.3, C2.4)
Moteur vectorisé (Rust), rapide sur un poste, sans cluster. **Pourquoi** : volumétrie
parisienne tient en mémoire ; évite la complexité d'un cluster pour la démo.

### 3. PostgreSQL (relationnel, couche Gold) + Cassandra (NoSQL) (C1.1, C1.2)
Couche Gold pour l'analytique structurée (tables de restitution, index). Cassandra pour les
événements de streaming (écritures append-only, tri par date, TTL 7 j). **Pourquoi** :
chaque base sur son point fort ; complémentarité SQL / NoSQL.

### 4. Sources réelles DVF + INSEE Filosofi (C2.3)
Prix immobilier réel (DVF 2023) et revenu médian réel (INSEE Filosofi 2020) chargés
par `etl/external.py`, avec repli sur des valeurs de référence si les fichiers sont
absents. Drapeau `data_source` (`real`/`reference`) pour la traçabilité. **Pourquoi** :
des chiffres réels crédibilisent les indicateurs ; le repli garde le mode hors ligne.

### 5. API FastAPI : JWT + quotas + filtres (C2.1)
OAuth2/JWT (rôles viewer/admin), quota par IP (anonyme 120, authentifié 600 req/min),
endpoints filtrables (arrondissement, score). Lecture publique conservée pour la démo.
**Pourquoi** : répond aux critères authentification + autorisations/quotas tout en
gardant le dashboard ouvert.

### 6. Résilience & scalabilité (C1.4)
Docker Compose, services à `restart: unless-stopped`, healthchecks (postgres, cassandra,
api), démarrage ordonné via `depends_on: condition: service_healthy`, volumes nommés
persistants. Profils `streaming` (Kafka) et `lake` (Hadoop/Hive) activables. Mode
local-first hors ligne comme filet de continuité. **Pourquoi** : continuité de service
et montée en charge progressive sans réécriture.

### 7. Interface aux codes DSFR (restitution)
Système de Design de l'État (Marianne, bleu France), fond IGN Géoplateforme, thèmes
clair/sombre, accessibilité WCAG AA. **Pourquoi** : crédibilité institutionnelle et
lisibilité, alignées sur un usage public des données.

## Conséquences

- Forces : couverture complète C1.1 à C2.4, données réelles, hors ligne, accessible.
- Limites assumées : HA non testée en conditions réelles (mono-poste de démo) ;
  authentification active mais lecture publique par choix de démonstration.
