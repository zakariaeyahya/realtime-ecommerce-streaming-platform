# Real-Time E-Commerce Streaming Analytics Platform

Plateforme d'analytics streaming temps reel pour e-commerce, avec detection de fraude, recommandations personnalisees et prevision d'inventaire.

## Resultats

- **177 tests** passent (0 echecs)
- **78% coverage** (objectif > 70%)
- **13 services Docker** orchestres
- **2.7M evenements** Retail Rocket integres

---

## Quick Start

### Prerequis

- Docker & Docker Compose
- Python 3.11+
- Git

### Installation

```bash
# Cloner le projet
git clone <repo-url>
cd PROJET-1

# Creer et activer le virtualenv
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Installer les dependances
pip install -r requirements.txt

# Configurer le chemin projet dans config/.env
# PROJECT_PATH=D:/grand projet/PROJET 1

# Demarrer les services Docker
docker-compose up -d

# Verifier que tout est healthy
docker-compose ps
```

### Lancer le pipeline Flink

```bash
docker exec streaming-jobmanager-1 sh -c "export PYTHONPATH=/flink && flink run -py /flink/jobs/flink_jobs/unified_streaming_job_simple.py"
```

### Lancer l'API FastAPI

```bash
uvicorn serving.api.main:app --host 0.0.0.0 --port 8000
```

### Interfaces Web

| Service | URL | Identifiants |
|---------|-----|--------------|
| API FastAPI (Swagger) | http://localhost:8000/docs | - |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| Kafka UI | http://localhost:8080 | - |
| Airflow | http://localhost:8082 | admin / admin |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| Flink Dashboard | http://localhost:8081 | - |

---

## Architecture

```
                    +---------------------------+
                    |   Kafka (Event Streaming)  |
                    |   5 topics, Avro schemas   |
                    +-----+------+------+-------+
                          |      |      |
                    +-----v-+ +--v---+ +v--------+
                    | Flink | | Flink| |  Flink   |
                    | Fraud | | Reco | | Inventory|
                    +-----+-+ +--+---+ +--+------+
                          |      |        |
                    +-----v------v--------v------+
                    |     Redis (Cache)           |
                    +----------+------------------+
                               |
                    +----------v------------------+
                    |   FastAPI (REST API)         |
                    |   /fraud  /reco  /inventory  |
                    +----------+------------------+
                               |
                    +----------v------------------+
                    | Prometheus + Grafana         |
                    | (Monitoring & Alertes)       |
                    +-----------------------------+
```

### Stack Technique

| Couche | Technologie |
|--------|------------|
| Streaming | Apache Kafka 7.5.0 (Confluent) |
| Processing | PyFlink 1.18.1 |
| ML | scikit-learn (RandomForest), joblib |
| Cache | Redis 7 |
| API | FastAPI + Uvicorn |
| Lakehouse | Apache Iceberg + dbt + MinIO |
| Orchestration | Apache Airflow 2.7.3 |
| Monitoring | Prometheus + Grafana |
| Containers | Docker Compose (13 services) |

---

## Structure du Projet

```
PROJET-1/
|
|-- config/                         # Configuration centralisee
|   |-- constants.py                # Constantes (seuils, ports, TTL)
|   |-- .env                        # Variables d'environnement
|   |-- kafka/topics.yaml           # 5 topics Kafka
|   +-- flink/flink-conf.yaml       # Config Flink
|
|-- ingestion/                      # Couche ingestion
|   |-- producer.py                 # Kafka producer (Avro)
|   |-- basic_consumer.py           # Consumer de test
|   |-- schemas.py                  # Schemas Python
|   |-- schema/                     # Schemas Avro (.avsc)
|   +-- loaders/                    # Chargeurs de datasets
|       |-- retail_rocket_loader.py # Retail Rocket (2.7M events)
|       |-- instacart_loader.py
|       +-- olist_loader.py
|
|-- processing/                     # Couche traitement (Flink)
|   |-- Dockerfile                  # Image Flink custom
|   |-- flink_jobs/
|   |   |-- fraud_detection.py      # Detection de fraude
|   |   |-- recommendations.py      # Recommandations
|   |   |-- inventory_forecasting.py# Prevision inventaire
|   |   |-- unified_streaming_job_simple.py
|   |   +-- utils/
|   |       |-- cache_manager.py    # Redis + fallback memoire
|   |       |-- feature_extractor.py# 90+ features
|   |       |-- feature_engineering.py
|   |       |-- forecasting_engine.py
|   |       |-- recommendation_engine.py
|   |       |-- model_loader.py
|   |       +-- time_series_features.py
|   +-- models/                     # Modeles ML (.pkl, .joblib)
|
|-- serving/                        # Couche API
|   |-- api/
|   |   |-- main.py                 # FastAPI (5 endpoints)
|   |   +-- models.py               # Modeles Pydantic
|   +-- consumers/
|       +-- kafka_consumers.py      # 3 consumers Kafka -> Redis
|
|-- lakehouse/                      # Couche analytique
|   |-- iceberg_setup/              # Init catalogue Iceberg
|   |-- spark_jobs/                 # Jobs Spark
|   +-- dbt_project/
|       |-- models/
|       |   |-- bronze/             # Donnees brutes
|       |   |-- silver/             # Donnees nettoyees
|       |   +-- gold/               # Dimensions & KPIs
|       +-- tests/                  # Tests de qualite dbt
|
|-- orchestration/                  # Orchestration
|   +-- dags/
|       +-- data_quality.py         # DAG qualite quotidien
|
|-- monitoring/                     # Monitoring
|   |-- prometheus/
|   |   |-- prometheus.yml          # Scrape config (4 targets)
|   |   +-- alert_rules.yml         # 7 regles d'alerte
|   +-- grafana/
|       |-- provisioning/           # Auto-config datasources
|       +-- dashboards/
|           +-- overview.json       # Dashboard unifie (20 panels)
|
|-- tests/                          # Tests
|   |-- conftest.py                 # Fixtures partagees
|   |-- unit/                       # 22 fichiers de tests
|   +-- integration/                # 7 fichiers de tests
|
|-- scripts/                        # Utilitaires
|   |-- load_real_data.py           # Chargement Retail Rocket
|   |-- train_fraud_model.py
|   |-- train_recommendation_model.py
|   |-- train_inventory_model.py
|   +-- evaluate_*.py               # Evaluation modeles
|
|-- docker-compose.yml              # 13 services
|-- setup.cfg                       # Config pytest + coverage
+-- README.md
```

---

## Fonctionnalites

### 1. Detection de Fraude (Flink)

- Fenetres tumbling de 5 minutes
- Extraction de 90+ features par transaction
- Modele RandomForest (precision 94%, rappel 89%)
- Score de fraude cache dans Redis, expose via API
- Latence < 500ms (p99)

### 2. Recommandations Personnalisees (Flink)

- Fenetres de session de 30 minutes
- Filtrage collaboratif (item-based)
- Top-K recommandations cachees dans Redis (TTL 1h)
- 30+ features utilisateur/produit

### 3. Prevision d'Inventaire (Flink)

- Fenetres glissantes de 24 heures
- 50+ features time-series
- Modele hybride Prophet (60%) + ARIMA (40%)
- Alertes de rupture de stock (seuil < 100 unites)
- Precision 87.5%, latence < 2s

### 4. API REST (FastAPI)

| Endpoint | Methode | Description |
|----------|---------|-------------|
| `/health` | GET | Etat des services (Redis, Kafka) |
| `/fraud/{user_id}` | GET | Score de fraude d'un utilisateur |
| `/recommendations/{user_id}` | GET | Recommandations personnalisees |
| `/inventory/{product_id}` | GET | Prevision de stock + alertes |
| `/metrics` | GET | Metriques Prometheus |

### 5. Lakehouse (Iceberg + dbt)

- **Bronze** : Donnees brutes Kafka (events, fraud_scores, inventory)
- **Silver** : Donnees nettoyees et deduplicees
- **Gold** : Dimensions (users, products) + KPIs business
- Stockage S3 via MinIO

### 6. Monitoring (Prometheus + Grafana)

- 4 targets scrapes : FastAPI, Flink, Redis, Prometheus
- 7 regles d'alerte (APIDown, RedisDown, FlinkJobFailed, etc.)
- Dashboard unifie avec 20 panels (services, API, Redis, KPIs)

### 7. Orchestration (Airflow)

- DAG `data_quality` : verification quotidienne (API, Redis, Kafka, dbt)

---

## Services Docker

| Service | Image | Port |
|---------|-------|------|
| Zookeeper | confluentinc/cp-zookeeper:7.5.0 | 2181 |
| Kafka | confluentinc/cp-kafka:7.5.0 | 9092 |
| Schema Registry | confluentinc/cp-schema-registry:7.5.0 | 8086 |
| Kafka UI | provectuslabs/kafka-ui | 8080 |
| Redis | redis:7-alpine | 6381 |
| Flink JobManager | custom (PyFlink 1.18.1) | 8081 |
| Flink TaskManager x2 | custom (PyFlink 1.18.1) | - |
| MinIO | minio/minio | 9010 / 9001 |
| Prometheus | prom/prometheus:v2.48.0 | 9090 |
| Redis Exporter | oliver006/redis_exporter | 9121 |
| Grafana | grafana/grafana:10.2.0 | 3000 |
| Airflow | apache/airflow:2.7.3-python3.11 | 8082 |

---

## Tests

```bash
# Tous les tests
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=. --cov-report=term-missing

# Tests unitaires seulement
pytest tests/unit/ -v

# Tests d'integration (Docker requis)
pytest tests/integration/ -v

# Test specifique
pytest tests/unit/test_fraud_detection.py -v
```

### Resultats actuels

```
177 passed, 3 skipped, 0 failed
Coverage: 78% (objectif > 70%)
Temps: ~17s
```

### Couverture par module

| Module | Coverage |
|--------|----------|
| config/ | 100% |
| serving/ | 87-100% |
| ingestion/ | 75-98% |
| processing/utils/ | 82-92% |
| processing/flink_jobs/ | 41-63% |

---

## Entrainement des Modeles

```bash
# Fraude
python scripts/train_fraud_model.py

# Recommandations
python scripts/train_recommendation_model.py

# Inventaire
python scripts/train_inventory_model.py

# Evaluation
python scripts/evaluate_recommendations.py
python scripts/evaluate_inventory_models.py
```

---

## Commandes Utiles

```bash
# Demarrer tous les services
docker-compose up -d

# Arreter tous les services
docker-compose down

# Voir les logs d'un service
docker-compose logs -f kafka

# Lister les topics Kafka
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Charger les donnees Retail Rocket
python scripts/load_real_data.py --source retail_rocket

# Lancer l'API
uvicorn serving.api.main:app --host 0.0.0.0 --port 8000
```

---

## Conventions

- **Python** : snake_case, PascalCase (classes), SCREAMING_SNAKE (constantes)
- **Logging** : uniquement `logging`, zero `print()`
- **Config** : `config/constants.py` + `os.getenv()` avec fallback
- **Git** : `type(scope): description` (feat/fix/docs/test/refactor/chore/perf)
- **Tests** : pytest, coverage > 70%, fixtures dans conftest.py
- **Fonctions** : < 30 lignes, type hints obligatoires

---

## Sprints

| Sprint | Contenu | Status |
|--------|---------|--------|
| 1 | Kafka producers/consumers + schemas Avro | Complete |
| 2 | Integration donnees (Retail Rocket 2.7M events) | Complete |
| 3 | Flink Fraud Detection | Complete |
| 4 | Recommandations personnalisees | Complete |
| 5 | Prevision d'inventaire | Complete |
| 6 | Lakehouse (Iceberg + dbt) | Partiel |
| 7 | API FastAPI (Serving Layer) | Complete |
| 8 | Docker + Monitoring + Orchestration | Complete |
