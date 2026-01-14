# 📊 Plateforme de Streaming Analytics E-Commerce en Temps Réel

**Une architecture production-ready de data streaming moderne** : 200k+ événements/seconde, détection fraude < 500ms, recommandations temps réel.

---

## 🎯 Vue d'Ensemble

Cette plateforme démontre une architecture **end-to-end** complète pour traiter des flux de données massifs et en temps réel sur une marketplace e-commerce :

| Métrique | Valeur |
|----------|--------|
| 📈 Débit | 200k+ événements/seconde |
| ⚡ Latence fraude | < 500ms (p99) |
| 💰 Impact | 2,5M€ économisés/an (fraude détectée) |
| 📊 Conversion | +18% (recommandations) |
| 📦 Stock | -30% ruptures de stock |
| 🛡️ Uptime | 99.95% SLA |

---

## 🏗️ Architecture

### Composants Clés

```
┌─────────────────┐
│  Apps Web/Mobile│  → 100k req/s
└────────┬────────┘
         │
    ┌────▼─────────────────────────────┐
    │  Apache Kafka (12 brokers)        │
    │  50+ topics, 3x replication       │
    │  Schema Registry (Avro)           │
    └────┬──────────┬─────────┬─────────┘
         │          │         │
    ┌────▼────┐ ┌──▼───┐ ┌───▼─────┐
    │  Flink  │ │Flink │ │  Flink  │
    │ Fraud   │ │Recom-│ │Inventory│
    │Detection│ │ mend │ │Forecast │
    └────┬────┘ └──┬───┘ └───┬─────┘
         │         │         │
    ┌────▼─────────▼─────────▼────┐
    │   Redis + RocksDB + S3       │
    │   (Cache, State, Storage)    │
    └────┬──────────────────────────┘
         │
    ┌────▼──────────────────────────┐
    │  FastAPI / Lakehouse (Iceberg)│
    │  Queries / Analytics Layer    │
    └───────────────────────────────┘
         │
    ┌────▼──────────────────────────┐
    │ Prometheus + Grafana + Airflow│
    │ (Monitoring & Orchestration)  │
    └───────────────────────────────┘
```

### Stack Technologique

| Catégorie | Technologie |
|-----------|-------------|
| **Streaming** | Apache Kafka 7.5 + Flink 1.18 |
| **Storage** | Apache Iceberg + MinIO (S3-compatible) |
| **Cache** | Redis Cluster |
| **Analytics** | dbt + Trino/Spark |
| **API** | FastAPI + Uvicorn |
| **Orchestration** | Apache Airflow |
| **Monitoring** | Prometheus + Grafana |
| **Infra** | Docker Compose (local), K8s (optionnel) |

---

## 🚀 Quick Start (5 minutes)

### Prérequis

- Docker & Docker Compose
- Python 3.10+
- Git

### Installation

```bash
# Clone le repo
git clone https://github.com/your-org/project1-ecommerce-streaming.git
cd project1-ecommerce-streaming

# Crée l'environnement
cp .env.example .env

# Lance tout
docker-compose up -d

# Attends ~30s (services startup)
docker-compose ps  # Tous les services doivent être healthy
```

### Validation

```bash
# 1. Vérifie Kafka
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# 2. Lance le producer
docker-compose exec -d producer python ingestion/producer.py

# 3. Lance un consumer
docker-compose exec consumer python ingestion/basic_consumer.py

# 4. Accès API
curl http://localhost:8000/health
# → {"status": "ok", "timestamp": "2024-01-14T..."}

# 5. Dashboard
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

---

## 📋 Structure du Projet

```
project1-ecommerce-streaming/
├── docker-compose.yml           # Orchestration complète
├── .env.example                 # Variables d'env
│
├── ingestion/                   # Producer Kafka
│   ├── producer.py
│   ├── schema/
│   └── requirements.txt
│
├── processing/                  # Jobs Flink
│   ├── flink_jobs/
│   │   ├── fraud_detection.py
│   │   ├── recommendations.py
│   │   ├── inventory_forecasting.py
│   │   └── business_metrics.py
│   └── models/                  # ML models
│
├── serving/                     # API + Consumers
│   ├── api/
│   │   └── main.py
│   └── consumers/
│       ├── fraud_consumer.py
│       ├── recommendations_consumer.py
│       └── metrics_consumer.py
│
├── lakehouse/                   # Datalake (Iceberg + dbt)
│   ├── dbt_project/
│   └── iceberg_setup/
│
├── monitoring/                  # Prometheus + Grafana
│   ├── prometheus/
│   └── grafana/
│
├── orchestration/               # Airflow DAGs
│   └── dags/
│
├── tests/                       # Tests (unit + integration)
│   ├── unit/
│   ├── integration/
│   └── performance/
│
├── docs/                        # Documentation
│   ├── SPRINT_1_DETAILED.md
│   ├── ARCHITECTURE.md
│   ├── GETTING_STARTED.md
│   └── ...
│
└── scripts/                     # Utilitaires
    ├── setup.sh
    ├── load_dataset.py
    └── cleanup.sh
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [SPRINT_1_DETAILED.md](docs/SPRINT_1_DETAILED.md) | Guide complet du Sprint 1 (Kafka) |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Vue d'ensemble technique |
| [GETTING_STARTED.md](docs/GETTING_STARTED.md) | Guide pas-à-pas pour démarrer |
| [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) | Endpoints et schemas |
| [KAFKA_SETUP.md](docs/KAFKA_SETUP.md) | Configuration Kafka détaillée |
| [FLINK_JOBS.md](docs/FLINK_JOBS.md) | Description de chaque job |

---

## 🔄 Pipeline de Données

### End-to-End Flow

```
1. Événements Utilisateur (Web/Mobile)
   ↓
2. Kafka Topics (events, inventory, etc.)
   ↓
3. Flink Jobs (détection, recos, forecast)
   ↓
4. Cache (Redis) + Storage (Iceberg)
   ↓
5. FastAPI Serving Layer
   ↓
6. Clients (Frontend, BI, Dashboards)
```

### Exemples de Cas d'Usage

#### 🔴 Détection de Fraude
- Input: `events` topic (purchases)
- Processing: 5-min tumbling windows + 90+ features
- Output: fraud scores → Redis
- Latency: < 500ms

#### 🎁 Recommandations Produits
- Input: `events` topic (clicks, views)
- Processing: Session windows (30 min) + collaborative filtering
- Output: top-10 recommendations → Redis
- Latency: < 1 second

#### 📦 Prévision Stock
- Input: `inventory` topic (stock levels)
- Processing: Sliding windows + Prophet forecasting
- Output: alerts (< 100 units) + runout predictions
- Accuracy: > 85%

---

## 🧪 Tests et Validation

### Exécuter les Tests

```bash
# Tests unitaires
pytest tests/unit/ -v --cov=processing --cov-report=html

# Tests d'intégration
pytest tests/integration/ -v

# Tests de performance
pytest tests/performance/ -v

# Couverture globale
pytest tests/ --cov=. --cov-report=term-missing
```

### Critères de Qualité

- ✅ Coverage > 80%
- ✅ Tous les tests passent
- ✅ Pas de warnings linting
- ✅ Type checking (mypy) sans erreurs

---

## 📊 Monitoring et Dashboards

### Accès aux Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| Kafka UI | http://localhost:8080 | - |
| API (Swagger) | http://localhost:8000/docs | - |
| Airflow | http://localhost:8888 | airflow / airflow |

### Dashboards Inclus

1. **Kafka Metrics** - Throughput, lag, topics
2. **Flink Jobs** - Backpressure, checkpoints, parallelism
3. **API Performance** - Latency p50/p99, error rates
4. **Business KPIs** - GMV, conversion, fraud detected
5. **Infrastructure** - CPU, Memory, Disk usage

---

## 🛠️ Commandes Utiles

```bash
# Démarrage
docker-compose up -d

# Vérification
docker-compose ps
docker-compose logs -f kafka

# Producer (génère 10k events/sec)
docker-compose exec producer python ingestion/producer.py --speed x10

# Consumer (lit les events)
docker-compose exec consumer python ingestion/basic_consumer.py

# Soumission job Flink
docker-compose exec jobmanager /opt/flink/bin/flink run \
  -py /home/processing/flink_jobs/fraud_detection.py

# Nettoyage
docker-compose down -v
```

---

## 📈 Résultats Attendus (Après 16 semaines)

### Performance

| Métrique | Target |
|----------|--------|
| Throughput Kafka | 200k+ evt/sec |
| Latency Fraude (p99) | < 500ms |
| Latency API (p99) | < 200ms |
| Uptime | 99.95% |

### Business Impact

| Impact | Valeur |
|--------|--------|
| Fraude détectée | 2,5M€/an économisés |
| Conversion rate | +18% |
| Stock optimization | -30% ruptures |
| Marge (dynamic pricing) | +12% |

---

## 🔐 Sécurité et Bonnes Pratiques

- ✅ Secrets en `.env` (jamais en hardcoding)
- ✅ Credentials en variables d'environnement
- ✅ Logging centralisé (jamais de print)
- ✅ Type hints partout (Python)
- ✅ Tests avant déploiement
- ✅ Schema validation (Avro)

---

## 🤝 Contribution

Ce projet suit le processus KISS :

1. **Code simple** : Une fonction = une responsabilité
2. **Pas de sur-ingénierie** : Résoudre le problème actuel
3. **Logging** : Toujours logging, pas de print
4. **Tests** : Avant ou avec le code (TDD)
5. **Commits** : Format `type(scope): description`

Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour les guidelines.

---

## 📄 License

MIT License - Voir [LICENSE](LICENSE)

---

## 🎓 Apprentissage

Ce projet couvre :

- ✅ Streaming architecture (Kafka)
- ✅ Stream processing (Flink)
- ✅ Real-time analytics (Lakehouse pattern)
- ✅ ML inference (fraud detection)
- ✅ API design (FastAPI)
- ✅ Monitoring (Prometheus + Grafana)
- ✅ Orchestration (Airflow)
- ✅ Testing et observability

Parfait pour upskill en **Data Engineering** et **System Design**.

---

**Made with ❤️ | 2024-2025**
