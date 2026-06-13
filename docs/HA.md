# Haute disponibilité · Urban Data Explorer

## Cassandra · passage à 3 nœuds

### Schéma actuel

Le keyspace `ude` utilise `NetworkTopologyStrategy` avec `replication_factor: 3`.
Cela signifie que chaque partition est répliquée sur **3 nœuds** du datacenter.

```cql
CREATE KEYSPACE IF NOT EXISTS ude
  WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 3};
```

### En développement local (1 nœud)

Cassandra accepte RF=3 sur un cluster mono-nœud : les données sont simplement
écrites sur le seul nœud disponible. Aucune erreur, aucun changement applicatif.

### Déploiement 3 nœuds (production)

1. Ajouter 3 services Cassandra dans docker-compose (seeds partagés) :

```yaml
cassandra-node1:
  image: cassandra:4.1
  restart: unless-stopped
  environment:
    - CASSANDRA_SEEDS=cassandra-node1,cassandra-node2,cassandra-node3
    - CASSANDRA_DC=datacenter1
    - CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch
  healthcheck:
    test: ["CMD-SHELL", "cqlsh -e 'describe keyspaces' || exit 1"]
    interval: 15s
    timeout: 10s
    retries: 12
    start_period: 90s
  volumes:
    - cassandradata1:/var/lib/cassandra

cassandra-node2:
  image: cassandra:4.1
  restart: unless-stopped
  environment:
    - CASSANDRA_SEEDS=cassandra-node1,cassandra-node2,cassandra-node3
    - CASSANDRA_DC=datacenter1
    - CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch
  depends_on:
    cassandra-node1:
      condition: service_healthy
  volumes:
    - cassandradata2:/var/lib/cassandra

cassandra-node3:
  image: cassandra:4.1
  restart: unless-stopped
  environment:
    - CASSANDRA_SEEDS=cassandra-node1,cassandra-node2,cassandra-node3
    - CASSANDRA_DC=datacenter1
    - CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch
  depends_on:
    cassandra-node2:
      condition: service_healthy
  volumes:
    - cassandradata3:/var/lib/cassandra
```

2. L'API se connecte à tous les nœuds en passant la liste complète :

```python
# api/db.py
hosts = os.getenv("CASSANDRA_HOST", "cassandra").split(",")
cluster = Cluster(hosts, port=int(os.getenv("CASSANDRA_PORT", "9042")))
```

3. Avec RF=3, le niveau de cohérence `QUORUM` (2/3 nœuds) tolère la perte
   d'un nœud sans interruption de service.

### `restart: unless-stopped` + healthchecks

Tous les services docker-compose ont `restart: unless-stopped` et un
`healthcheck` configuré. L'API ne démarre qu'après que Cassandra et
PostgreSQL ont passé leur sonde (`condition: service_healthy`).

## PostgreSQL · résilience

Le service `postgres` utilise le volume persistant `pgdata` ; les données
survivent à un `docker compose down` (sans `--volumes`).

Pour un PostgreSQL HA (primary + standby), envisager **Patroni** +
**HAProxy** sur un cluster dédié. Hors scope de cette démo RNCP.
