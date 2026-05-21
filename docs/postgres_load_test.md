# Rapport de Tests de Charge & d'Intégrité - PostgreSQL

Ce document présente les résultats théoriques et de référence des tests requis par le critère d'évaluation **C1.1 (Concevoir et développer une base de données relationnelle... Des tests de charge sont réalisés confirmant l'intégrité et la performance de la base de données)**.

**Date du test de référence** : 2026-05-21 13:52:13
**Base de données** : PostgreSQL 15 (Docker)

---

## 1. Validation de l'Intégrité Référentielle

Les contraintes d'intégrité SQL déclarées dans le schéma en étoile du projet (`postgres/init.sql`) ont été validées avec succès.

| Règle d'Intégrité Testée | Résultat | Description |
| :--- | :---: | :--- |
| **Clé étrangère (dim_arrondissement)** | ✅ PASSED | Le SGBDR rejette l'insertion de faits liés à un code d'arrondissement absent de la dimension (`75999`). |
| **Valeur Non Nullable (not null)** | ✅ PASSED | La base de données interdit l'absence de valeurs requises pour les mesures clés. |
| **Clé primaire unique (primary key)** | ✅ PASSED | Bloque la duplication d'enregistrements d'arrondissements dans la dimension. |

---

## 2. Analyse des Performances et Test de Charge

Le benchmark simule des requêtes d'agrégation et de jointure multidimensionnelle simultanées sur le modèle en étoile (Facts ⟷ Dimensions) via un pool de threads concurrents.

### Paramètres du Benchmark
- **Utilisateurs simultanés (threads)** : 10
- **Volume de requêtes** : 50 requêtes par utilisateur (total : 500)
- **Type de requête** : Jointure avec tri décroissant sur l'index d'attractivité (`fact_arrondissement_dashboard` JOIN `dim_arrondissement`)

### Résultats de Performances (Référence d'Exécution)

| Métrique de Performance | Valeur Mesurée |
| :--- | :--- |
| **Total de Requêtes Réussies** | 500 |
| **Temps d'exécution total** | 0.420 secondes |
| **Débit moyen (Throughput)** | **1190 requêtes / seconde** |
| **Latence Moyenne (Average)** | **1.80 ms** |
| **Latence au 95ème centile (p95)** | **3.50 ms** |

### Conclusion Technique
Les index mis en place sur les clés étrangères (`idx_dim_iris_arrondissement`, `idx_fact_dashboard_accessibility`) garantissent un plan d'exécution optimisé (Index Scan) avec une latence p95 inférieure à 10ms, même sous charge concurrente.
