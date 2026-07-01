"""Test de charge et d'intégrité PostgreSQL - Projet Urban Data Explorer.

C1.1 : Des tests de charge sont réalisés confirmant l'intégrité et la performance
de la base de données (couche relationnelle Gold).
"""

from __future__ import annotations

import os
import time
import concurrent.futures
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2 import errors

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")  # local/docker
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "ude")
POSTGRES_USER = os.getenv("POSTGRES_USER", "ude")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ude")

CONCURRENT_USERS = 10
QUERIES_PER_USER = 50
DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"

def get_connection():
    import pytest
    try:
        return psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )
    except psycopg2.OperationalError:
        pytest.skip(
            "PostgreSQL indisponible -- test d'integration ignore "
            "(necessite la base live, ex. docker-compose up postgres)."
        )

def test_integrity():
    """Vérifie le respect des contraintes d'intégrité de la base de données."""
    print("  -> Lancement des tests d'intégrité...")
    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    checks = {
        "Clé étrangère (dim_arrondissement)": False,
        "Valeur Non Nullable (not null)": False,
        "Clé primaire unique (primary key)": False
    }

    # 1. Clé étrangère : tentative d'insérer un arrondissement invalide (75999) dans les faits
    try:
        cur.execute(
            "INSERT INTO fact_arrondissement_dashboard (arrondissement_code, green_space_count) "
            "VALUES ('75999', 10)"
        )
        conn.commit()
    except errors.ForeignKeyViolation:
        checks["Clé étrangère (dim_arrondissement)"] = True
        conn.rollback()
    except Exception as e:
        print(f"     [WARN] Erreur inattendue FK check: {e}")
        conn.rollback()

    # 2. Valeur Non Nullable : tentative d'insérer un record avec un champ requis NULL
    try:
        cur.execute(
            "INSERT INTO fact_arrondissement_dashboard (arrondissement_code, green_space_count) "
            "VALUES ('75001', NULL)"
        )
        conn.commit()
    except errors.NotNullViolation:
        checks["Valeur Non Nullable (not null)"] = True
        conn.rollback()
    except Exception as e:
        print(f"     [WARN] Erreur inattendue NOT NULL check: {e}")
        conn.rollback()

    # 3. Clé primaire unique : tentative d'insérer un code existant en doublon
    try:
        # On essaie d'insérer 75001 à nouveau (déjà présent car initialisé)
        cur.execute(
            "INSERT INTO dim_arrondissement (code_arrondissement, label, name) "
            "VALUES ('75001', 'Paris 1er', 'Louvre')"
        )
        conn.commit()
    except errors.UniqueViolation:
        checks["Clé primaire unique (primary key)"] = True
        conn.rollback()
    except Exception as e:
        print(f"     [WARN] Erreur inattendue PK check: {e}")
        conn.rollback()

    conn.close()
    return checks

def execute_user_session(user_id: int) -> tuple[int, list[float]]:
    """Simule les requêtes analytiques d'un utilisateur concurrent sur les jointures."""
    latencies = []
    success_count = 0
    
    # Requête de restitution Gold (agrégats relationnels)
    query = """
        SELECT 
            da.label, 
            da.name, 
            fd.accessibility_index, 
            fd.pressure_index, 
            fd.attractiveness_index
        FROM fact_arrondissement_dashboard fd
        JOIN dim_arrondissement da ON fd.arrondissement_code = da.code_arrondissement
        ORDER BY fd.attractiveness_index DESC
    """
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        for _ in range(QUERIES_PER_USER):
            start = time.perf_counter()
            cur.execute(query)
            cur.fetchall()
            latencies.append(time.perf_counter() - start)
            success_count += 1
        cur.close()
        conn.close()
    except Exception as e:
        print(f"     [ERROR] Session utilisateur {user_id} en échec: {e}")
        
    return success_count, latencies

def run_load_test():
    """Exécute le test de charge multi-threadé."""
    print(f"  -> Lancement du test de charge ({CONCURRENT_USERS} utilisateurs, {QUERIES_PER_USER} requêtes chacun)...")
    
    start_time = time.perf_counter()
    all_latencies = []
    total_success = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(execute_user_session, i) for i in range(CONCURRENT_USERS)]
        for future in concurrent.futures.as_completed(futures):
            success, latencies = future.result()
            total_success += success
            all_latencies.extend(latencies)
            
    total_time = time.perf_counter() - start_time
    
    if not all_latencies:
        return None
        
    avg_latency = (sum(all_latencies) / len(all_latencies)) * 1000  # ms
    throughput = total_success / total_time  # req/sec
    p95_latency = sorted(all_latencies)[int(len(all_latencies) * 0.95)] * 1000  # ms
    
    return {
        "total_requests": total_success,
        "total_time_seconds": total_time,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "throughput_req_sec": throughput
    }

def main():
    print("=" * 60)
    print("  PostgreSQL Load & Integrity Testing Tool")
    print("=" * 60)

    # 1. Vérifier si Postgres est accessible
    try:
        conn = get_connection()
        conn.close()
    except Exception as e:
        print("\n  [WARN] Impossible de se connecter à PostgreSQL.")
        print("  Garantissez que la base PostgreSQL est lancée (docker-compose up -d postgres).")
        print("  Création d'un rapport de démonstration théorique par défaut...")
        generate_mock_report()
        return

    # 2. Exécution des tests d'intégrité
    integrity_results = test_integrity()
    for check, passed in integrity_results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"     [INFO] {check}: {status}")

    # 3. Exécution du test de charge
    load_results = run_load_test()
    if load_results:
        print("\n  Résultats des performances :")
        print(f"     - Requêtes exécutées : {load_results['total_requests']}")
        print(f"     - Débit (Throughput) : {load_results['throughput_req_sec']:.2f} req/s")
        print(f"     - Latence moyenne    : {load_results['avg_latency_ms']:.2f} ms")
        print(f"     - Latence 95e centile: {load_results['p95_latency_ms']:.2f} ms")
    
    # 4. Génération du fichier de rapport markdown (conclusions calculées)
    generate_markdown_report(integrity_results, load_results)

def generate_markdown_report(integrity, load):
    DOCS_DIR.mkdir(exist_ok=True)
    report_path = DOCS_DIR / "postgres_load_test.md"
    
    content = f"""# Rapport de Tests de Charge & d'Intégrité - PostgreSQL

Ce document présente les résultats des tests requis par le critère d'évaluation **C1.1 (Concevoir et développer une base de données relationnelle... Des tests de charge sont réalisés confirmant l'intégrité et la performance de la base de données)**.

**Date du test** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Base de données** : PostgreSQL 15+

---

## 1. Validation de l'Intégrité Référentielle

Nous avons testé activement les contraintes SQL déclarées dans le schéma en étoile du projet (`postgres/init.sql`).

| Règle d'Intégrité Testée | Résultat | Description |
| :--- | :---: | :--- |
| **Clé étrangère (dim_arrondissement)** | {"✅ PASSED" if integrity["Clé étrangère (dim_arrondissement)"] else "❌ FAILED"} | Le SGBDR rejette l'insertion de faits liés à un code d'arrondissement absent de la dimension (`75999`). |
| **Valeur Non Nullable (not null)** | {"✅ PASSED" if integrity["Valeur Non Nullable (not null)"] else "❌ FAILED"} | La base interdit l'absence de valeurs requises comme les comptages d'infrastructures. |
| **Clé primaire unique (primary key)** | {"✅ PASSED" if integrity["Clé primaire unique (primary key)"] else "❌ FAILED"} | Tentative d'insertion d'un doublon sur `code_arrondissement` bloquée à l'écriture. |

---

## 2. Analyse des Performances et Test de Charge

Le test simule des requêtes d'agrégation et de jointure multidimensionnelle simultanées sur le modèle en étoile (Facts ⟷ Dimensions) via un pool de threads concurrents.

### Paramètres du Benchmark
- **Utilisateurs simultanés (threads)** : {CONCURRENT_USERS}
- **Volume de requêtes** : {QUERIES_PER_USER} requêtes par utilisateur (total : {CONCURRENT_USERS * QUERIES_PER_USER})
- **Type de requête** : Jointure avec tri décroissant sur l'index d'attractivité (`fact_arrondissement_dashboard` JOIN `dim_arrondissement`)

### Résultats de Performances

| Métrique de Performance | Valeur Mesurée |
| :--- | :--- |
| **Total de Requêtes Réussies** | {load['total_requests']} |
| **Temps d'exécution total** | {load['total_time_seconds']:.3f} secondes |
| **Débit moyen (Throughput)** | **{load['throughput_req_sec']:.2f} requêtes / seconde** |
| **Latence Moyenne (Average)** | **{load['avg_latency_ms']:.2f} ms** |
| **Latence au 95ème centile (p95)** | **{load['p95_latency_ms']:.2f} ms** |

### Conclusion Technique
{"✅ Performances acceptables" if load["p95_latency_ms"] < 50 else "⚠️ Latence p95 élevée"} : latence p95 mesurée à {load["p95_latency_ms"]:.2f} ms sous {CONCURRENT_USERS} sessions concurrentes ({load["throughput_req_sec"]:.1f} req/s).
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n  [OK] Rapport écrit dans: {report_path}")

def generate_mock_report():
    """Génère un rapport simulé clairement labellisé – aucune mesure réelle n'est inventée."""
    DOCS_DIR.mkdir(exist_ok=True)
    report_path = DOCS_DIR / "postgres_load_test.md"

    content = f"""# Rapport de Tests de Charge & d'Intégrité - PostgreSQL

> **SIMULATION** : PostgreSQL était inaccessible lors de la génération de ce rapport.
> Aucune valeur de performance n'a été mesurée. Lancez `docker-compose up -d postgres`
> puis relancez ce script pour obtenir des mesures réelles.

Ce document concerne le critère **C1.1 (Concevoir et développer une base de données
relationnelle... Des tests de charge sont réalisés confirmant l'intégrité et la
performance de la base de données)**.

**Date de génération** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode** : Simulation (PostgreSQL non disponible)

---

## 1. Validation de l'Intégrité Référentielle

Les tests de contraintes SQL (`postgres/init.sql`) **n'ont pas pu s'exécuter** faute
de connexion. Les règles à valider sont :

| Règle d'Intégrité | Attendu | Statut |
| :--- | :--- | :--- |
| Clé étrangère (dim_arrondissement) | Rejet insertion code 75999 | Non mesuré |
| Valeur Non Nullable | Rejet NULL sur green_space_count | Non mesuré |
| Clé primaire unique | Rejet doublon code_arrondissement | Non mesuré |

---

## 2. Test de Charge

Le test de charge **n'a pas pu s'exécuter**. Paramètres prévus :
- Utilisateurs simultanés : {CONCURRENT_USERS}
- Requêtes par utilisateur : {QUERIES_PER_USER} (total : {CONCURRENT_USERS * QUERIES_PER_USER})
- Type : jointure fact_arrondissement_dashboard JOIN dim_arrondissement

Relancez le script avec PostgreSQL actif pour obtenir des mesures réelles.
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [OK] Rapport de simulation écrit dans: {report_path}")

if __name__ == "__main__":
    main()
