# Configuration Kafka - Guide Complet

## Architecture Kafka

### Composants

1. **Zookeeper**: Coordination et gestion du cluster Kafka
2. **Kafka Broker**: Serveur de messages (1 broker en local, 3+ en production)
3. **Schema Registry**: Gestion des schémas Avro
4. **Kafka UI**: Interface de monitoring (optionnel)

## Configuration des Topics

### Topics Créés

Tous les topics sont définis dans `config/kafka/topics.yaml`:

| Topic | Partitions | Retention | Usage |
|-------|------------|-----------|-------|
| raw-events | 3 | 7 jours | Événements e-commerce bruts |
| inventory-changes | 2 | 30 jours | Changements d'inventaire |
| fraud-scores | 2 | 7 jours | Scores de fraude |
| recommendations | 2 | 24 heures | Recommandations produits |
| business-metrics | 1 | 30 jours | Métriques business |

### Création Manuelle d'un Topic

```bash
docker exec ecommerce-kafka kafka-topics \
  --create \
  --bootstrap-server localhost:9092 \
  --topic my-custom-topic \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000
```

### Modification d'un Topic

```bash
# Augmenter le nombre de partitions
docker exec ecommerce-kafka kafka-topics \
  --alter \
  --bootstrap-server localhost:9092 \
  --topic raw-events \
  --partitions 6

# Modifier la rétention
docker exec ecommerce-kafka kafka-configs \
  --alter \
  --bootstrap-server localhost:9092 \
  --topic raw-events \
  --add-config retention.ms=1209600000
```

### Suppression d'un Topic

```bash
docker exec ecommerce-kafka kafka-topics \
  --delete \
  --bootstrap-server localhost:9092 \
  --topic my-topic
```

## Configuration Producer

### Paramètres Importants

Dans `config/constants.py`:

```python
PRODUCER_CONFIG = {
    'bootstrap.servers': 'localhost:9092',
    'acks': 'all',                    # Garantie de durabilité maximale
    'retries': 3,                     # Nombre de tentatives
    'max.in.flight.requests.per.connection': 1,  # Ordre garanti
    'compression.type': 'snappy',     # Compression efficace
    'linger.ms': 10,                  # Batch messages pendant 10ms
    'batch.size': 16384,              # Taille du batch en bytes
}
```

### Garanties de Livraison

- **acks='all'**: Attend confirmation de tous les replicas
- **retries=3**: Réessaye 3 fois en cas d'échec
- **idempotence=True**: Évite les duplications (à activer en prod)

## Configuration Consumer

### Paramètres Importants

```python
CONSUMER_CONFIG = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'ecommerce-consumer-group',
    'auto.offset.reset': 'earliest',  # Lire depuis le début
    'enable.auto.commit': True,       # Commit automatique des offsets
    'auto.commit.interval.ms': 5000,  # Intervalle de commit
    'session.timeout.ms': 30000,      # Timeout de session
}
```

### Gestion des Offsets

#### Voir les offsets d'un consumer group

```bash
docker exec ecommerce-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group ecommerce-consumer-group \
  --describe
```

#### Reset des offsets

```bash
# Reset au début du topic
docker exec ecommerce-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group ecommerce-consumer-group \
  --topic raw-events \
  --reset-offsets --to-earliest \
  --execute

# Reset à un timestamp spécifique
docker exec ecommerce-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group ecommerce-consumer-group \
  --topic raw-events \
  --reset-offsets --to-datetime 2024-01-01T00:00:00.000 \
  --execute
```

## Monitoring

### Métriques Kafka

```bash
# Vérifier l'état du cluster
docker exec ecommerce-kafka kafka-broker-api-versions \
  --bootstrap-server localhost:9092

# Voir les consumer groups actifs
docker exec ecommerce-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list

# Voir le lag d'un consumer group
docker exec ecommerce-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group ecommerce-consumer-group \
  --describe
```

### Console Consumer (Debug)

```bash
# Lire les messages d'un topic
docker exec ecommerce-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic raw-events \
  --from-beginning \
  --max-messages 10
```

## Performance

### Optimisations Producer

```python
# High-throughput
PRODUCER_CONFIG = {
    'linger.ms': 100,           # Attendre plus longtemps avant d'envoyer
    'batch.size': 131072,       # Batches plus grands (128KB)
    'compression.type': 'lz4',  # Compression plus rapide
    'buffer.memory': 67108864,  # Buffer de 64MB
}

# Low-latency
PRODUCER_CONFIG = {
    'linger.ms': 0,             # Envoyer immédiatement
    'batch.size': 1,            # Pas de batching
    'compression.type': 'none', # Pas de compression
}
```

### Optimisations Consumer

```python
# Consommation rapide
CONSUMER_CONFIG = {
    'fetch.min.bytes': 50000,        # Récupérer au moins 50KB
    'fetch.max.wait.ms': 500,        # Attendre max 500ms
    'max.poll.records': 1000,        # Récupérer 1000 messages max
    'enable.auto.commit': False,     # Commit manuel pour contrôle
}
```

## Sécurité (Production)

### SSL/TLS

```python
PRODUCER_CONFIG = {
    'security.protocol': 'SSL',
    'ssl.ca.location': '/path/to/ca-cert',
    'ssl.certificate.location': '/path/to/client-cert',
    'ssl.key.location': '/path/to/client-key',
}
```

### SASL Authentication

```python
PRODUCER_CONFIG = {
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': 'your-username',
    'sasl.password': 'your-password',
}
```

## Troubleshooting

Voir `docs/TROUBLESHOOTING.md` pour les problèmes courants.

## Ressources

- [Documentation Confluent Kafka](https://docs.confluent.io/)
- [Kafka Python Client](https://docs.confluent.io/kafka-clients/python/current/overview.html)
- [Kafka Best Practices](https://kafka.apache.org/documentation/#bestpractices)
