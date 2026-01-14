# Architecture - Sprint 1: Ingestion Kafka

## Vue d'Ensemble

Le Sprint 1 implémente une architecture d'ingestion de données en temps réel basée sur Apache Kafka pour une plateforme e-commerce.

```
┌─────────────────┐
│  Data Sources   │
│  (Producer)     │
├─────────────────┤
│ - Synthetic     │
│ - Retail Rocket │
│ - Web Events    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Apache Kafka   │
│  (Message Bus)  │
├─────────────────┤
│ Topics:         │
│ • raw-events    │
│ • inventory     │
│ • fraud-scores  │
│ • recommend.    │
│ • metrics       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Consumers     │
│  (Processing)   │
├─────────────────┤
│ - Validation    │
│ - Storage       │
│ - Analytics     │
└─────────────────┘
```

## Composants

### 1. Producer Kafka (`ingestion/producer.py`)

**Responsabilités:**
- Génération d'événements e-commerce synthétiques
- Sérialisation en JSON
- Envoi vers topics Kafka avec retry logic
- Support du speed multiplier (1x, 10x, 100x)

**Types d'Événements Générés:**
- `view`: Consultation de produit (50%)
- `addtocart`: Ajout au panier (20%)
- `transaction`: Achat (10%)
- `search`: Recherche (10%)
- `filter`: Filtrage (7%)
- `review`: Avis client (3%)

**Configuration:**
```python
PRODUCER_CONFIG = {
    'acks': 'all',           # Durabilité maximale
    'retries': 3,            # Résilience
    'compression': 'snappy', # Performance
}
```

### 2. Consumer Kafka (`ingestion/basic_consumer.py`)

**Responsabilités:**
- Consommation des événements depuis Kafka
- Validation des schémas (champs obligatoires)
- Logging structuré
- Gestion des offsets

**Validation:**
- Vérification des champs obligatoires par type d'événement
- Rejet des événements malformés
- Compteurs de métriques (valides/invalides)

### 3. Infrastructure Kafka (Docker Compose)

**Services:**

#### Zookeeper
- Port: 2181
- Rôle: Coordination du cluster Kafka

#### Kafka Broker
- Port: 9092
- Partitions par topic: 1-3
- Replication factor: 1 (dev), 3+ (prod)

#### Schema Registry
- Port: 8081
- Rôle: Gestion des schémas Avro (Sprint 2+)

#### Kafka UI
- Port: 8080
- Rôle: Monitoring et debugging

## Flux de Données

### Flux Principal (Event Streaming)

```
1. EVENT GENERATION
   │
   ├─→ producer.generate_event()
   │   ├─→ Sélection du type (weighted random)
   │   ├─→ Génération des champs (Faker)
   │   └─→ Ajout du timestamp
   │
2. SERIALIZATION
   │
   ├─→ JSON encoding
   ├─→ UTF-8 encoding
   └─→ user_id as key (partitioning)
   │
3. KAFKA PUBLISH
   │
   ├─→ Topic routing (raw-events)
   ├─→ Partition assignment (hash(user_id))
   └─→ Delivery callback
   │
4. KAFKA STORAGE
   │
   ├─→ Append to partition log
   ├─→ Replication (if configured)
   └─→ Retention policy (7-30 days)
   │
5. CONSUMPTION
   │
   ├─→ consumer.poll()
   ├─→ Deserialization (JSON)
   ├─→ Validation
   └─→ Processing/Logging
```

### Flux de Validation

```
┌──────────────┐
│ Raw Message  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Decode UTF-8 │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Parse JSON   │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Validate Schema  │
│ • event_type     │
│ • required fields│
└──────┬───────────┘
       │
       ├─→ VALID ────→ Process
       │
       └─→ INVALID ──→ Log + Reject
```

## Configuration Centralisée

### `config/constants.py`

Toutes les configurations sont externalisées:

```python
# Kafka
KAFKA_BROKERS
KAFKA_TOPICS
PRODUCER_CONFIG
CONSUMER_CONFIG

# Data Generation
EVENT_TYPES
EVENT_TYPE_WEIGHTS
PRODUCT_CATEGORIES
PRICE_RANGES

# Logging
LOG_LEVEL
LOG_FORMAT
```

### `.env` (Variables d'environnement)

```bash
KAFKA_BROKERS=localhost:9092
PRODUCER_SPEED=1.0
CONSUMER_GROUP_ID=ecommerce-consumer-group
LOG_LEVEL=INFO
```

## Schémas de Données

### Événement View

```json
{
  "event_id": "uuid",
  "event_type": "view",
  "timestamp": 1704067200000,
  "user_id": "12345",
  "item_id": "9876",
  "category": "Electronics",
  "session_id": "session-abc",
  "device_type": "mobile"
}
```

### Événement Transaction

```json
{
  "event_id": "uuid",
  "event_type": "transaction",
  "timestamp": 1704067200000,
  "user_id": "12345",
  "item_id": "9876",
  "category": "Electronics",
  "price": 599.99,
  "quantity": 2
}
```

## Patterns de Design

### 1. Producer Pattern
- **Factory Pattern**: Génération d'événements par type
- **Callback Pattern**: Delivery confirmation asynchrone
- **Retry Pattern**: Tentatives automatiques en cas d'échec

### 2. Consumer Pattern
- **Poll Loop**: Boucle de consommation continue
- **Validation Pattern**: Vérification avant traitement
- **Offset Management**: Commit automatique ou manuel

### 3. Configuration Pattern
- **Environment Variables**: Configuration externalisée
- **Constants Module**: Point unique de vérité
- **Type Hints**: Documentation et validation statique

## Scalabilité

### Horizontal Scaling

**Producer:**
- Plusieurs instances parallèles
- Partitioning par user_id
- Load balancing automatique

**Consumer:**
- Consumer Group avec plusieurs instances
- Chaque partition assignée à un consumer
- Rebalancing automatique

**Exemple:**
```
Topic raw-events (3 partitions)
├─→ Partition 0 → Consumer A
├─→ Partition 1 → Consumer B
└─→ Partition 2 → Consumer C
```

### Vertical Scaling

**Optimisations:**
- Batching des messages (linger.ms)
- Compression (snappy)
- Buffering (batch.size)

## Résilience

### Producer
- Retry automatique (3 tentatives)
- Acks='all' (durabilité maximale)
- Idempotence (évite duplications)

### Consumer
- Auto-commit des offsets
- Session timeout avec rebalancing
- Error handling avec logging

### Infrastructure
- Healthchecks Docker
- Replication Kafka (production)
- Retention policy (backup temporel)

## Monitoring

### Métriques Clés

**Producer:**
- events_sent
- events_failed
- throughput (events/sec)

**Consumer:**
- messages_consumed
- messages_invalid
- consumer lag

**Kafka:**
- Topic size
- Partition count
- Consumer group lag

## Évolutions Futures

### Sprint 2: Avro Serialization
- Schémas Avro stricts
- Schema Registry integration
- Backward compatibility

### Sprint 3: Stream Processing
- Kafka Streams
- Aggregations en temps réel
- Windowing

### Sprint 4: Fraud Detection
- ML scoring en temps réel
- Fraud topic
- Alerting

## Références

- [Kafka Architecture](https://kafka.apache.org/documentation/#design)
- [Confluent Best Practices](https://docs.confluent.io/platform/current/kafka/deployment.html)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
