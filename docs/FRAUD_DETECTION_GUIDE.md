# Guide - Fraud Detection

## Vue d'ensemble

Le module de detection de fraude analyse les transactions e-commerce en temps reel via PyFlink, extrait 90+ features, et score chaque transaction avec un modele RandomForest.

## Architecture

```
Kafka (ecommerce-events)
    |
    v
Flink Fraud Detection Job
    |-> Fenetre Tumbling 5 min
    |-> Feature Extractor (90+ features)
    |-> RandomForest Model (.pkl)
    |-> Score Evaluator (seuil 0.85)
    |
    v
Kafka (fraud-scores) -> FraudConsumer -> Redis (fraud:{user_id})
    |
    v
FastAPI GET /fraud/{user_id}
```

## Composants

### FraudDetectionJob (`processing/flink_jobs/fraud_detection.py`)

Job principal qui :
1. Cree l'environnement Flink (parallelisme 4, checkpoint 30s)
2. Lit les evenements depuis Kafka
3. Applique une fenetre tumbling de 5 minutes
4. Extrait les features et score les transactions
5. Publie les alertes dans le topic `fraud-scores`

```python
from processing.flink_jobs.fraud_detection import FraudDetectionJob

job = FraudDetectionJob()
result = job.detect_fraud(features_dict)
# {'fraud_score': 0.92, 'is_fraud': True, 'timestamp': '...'}
```

### Feature Extractor (`processing/flink_jobs/utils/feature_extractor.py`)

Extrait 90+ features par transaction :

| Categorie | Exemples | Nombre |
|-----------|----------|--------|
| Montant | moyen, max, min, ecart-type | 10+ |
| Frequence | transactions/heure, /jour | 8+ |
| Temporel | heure du jour, jour semaine | 10+ |
| Comportement | categories visitees, panier moyen | 15+ |
| Device | type appareil, OS, navigateur | 8+ |
| Geolocation | pays, ville, distance | 10+ |
| Velocite | tx/heure, changement IP | 12+ |
| Historique | ratio vs historique, anomalies | 17+ |

### Feature Engineering (`processing/flink_jobs/utils/feature_engineering.py`)

Transformations supplementaires :
- Normalisation des features numeriques
- Encodage des features categorielles
- Calcul de ratios et ecarts

### Model Loader (`processing/flink_jobs/utils/model_loader.py`)

Charge le modele ML depuis le fichier pickle :
- Chemin : `processing/models/fraud_model.pkl`
- Format : scikit-learn RandomForest
- Configurable via `FRAUD_MODEL_PATH`

## Configuration

| Constante | Valeur | Description |
|-----------|--------|-------------|
| FRAUD_THRESHOLD | 0.85 | Score au-dessus duquel une transaction est frauduleuse |
| FRAUD_MIN_FEATURES | 90 | Nombre minimum de features requises |
| FRAUD_MODEL_PATH | processing/models/fraud_model.pkl | Chemin du modele |
| FLINK_WINDOW_SIZE_SECONDS | 300 | Taille de fenetre (5 min) |
| FLINK_PARALLELISM | 4 | Parallelisme Flink |
| FLINK_CHECKPOINT_INTERVAL_MS | 30000 | Interval checkpoint (30s) |

## Entrainement du modele

```bash
python scripts/train_fraud_model.py
```

Ce script :
1. Charge les donnees d'entrainement
2. Extrait les features
3. Entraine un RandomForest
4. Sauvegarde le modele dans `processing/models/fraud_model.pkl`

## Performance

| Metrique | Valeur |
|----------|--------|
| Precision | 94% |
| Rappel | 89% |
| Latence (p99) | < 500ms |
| Features | 90+ |

## API

```
GET /fraud/{user_id}

Reponse:
{
  "user_id": "user_1002",
  "fraud_score": 0.92,
  "is_fraud": true,
  "amount": 1500.0,
  "alert": "ALERT: High fraud risk (0.92)"
}
```

## Tests

```bash
# Tests unitaires
pytest tests/unit/test_fraud_detection.py -v
pytest tests/unit/test_feature_extractor.py -v
pytest tests/unit/test_feature_engineering.py -v

# Tests d'integration
pytest tests/integration/test_flink_fraud_job.py -v
```
