# API Documentation - FastAPI Serving Layer

## Vue d'ensemble

L'API REST expose les resultats du pipeline streaming via FastAPI. Les donnees sont lues depuis Redis (cache) ou les resultats sont stockes par les Kafka consumers en arriere-plan.

- **Framework** : FastAPI + Uvicorn
- **Port** : 8000
- **Swagger UI** : http://localhost:8000/docs
- **Metriques** : Prometheus (Counter + Histogram)

## Demarrage

```bash
# Demarrer Redis (via Docker)
docker-compose up -d redis

# Lancer l'API
uvicorn serving.api.main:app --host 0.0.0.0 --port 8000
```

Au demarrage, l'API :
1. Se connecte a Redis
2. Lance 3 Kafka consumers en threads background (fraude, recommandations, inventaire)
3. Expose les endpoints REST

---

## Endpoints

### GET /health

Verifie l'etat de l'API, Redis et Kafka.

**Reponse 200 :**

```json
{
  "status": "healthy",
  "redis": {
    "connected": true,
    "latency_ms": 1.23
  },
  "kafka": {
    "connected": true,
    "latency_ms": 45.67
  },
  "uptime": 3600.5
}
```

| Champ | Type | Description |
|-------|------|-------------|
| status | string | "healthy" ou "degraded" |
| redis.connected | bool | Connexion Redis active |
| redis.latency_ms | float | Latence ping Redis (ms) |
| kafka.connected | bool | Connexion Kafka active |
| kafka.latency_ms | float | Latence list_topics Kafka (ms) |
| uptime | float | Secondes depuis le demarrage |

---

### GET /fraud/{user_id}

Retourne le score de fraude d'un utilisateur.

**Parametres :**

| Parametre | Type | Description |
|-----------|------|-------------|
| user_id | string (path) | Identifiant utilisateur |

**Reponse 200 :**

```json
{
  "user_id": "user_1002",
  "fraud_score": 0.92,
  "is_fraud": true,
  "amount": 1500.0,
  "alert": "ALERT: High fraud risk (0.92)",
  "timestamp": "2024-01-15T10:30:00"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| user_id | string | Identifiant utilisateur |
| fraud_score | float (0-1) | Score de fraude |
| is_fraud | bool | true si score >= 0.85 (FRAUD_THRESHOLD) |
| amount | float | Montant de la transaction |
| alert | string/null | Message d'alerte si fraude detectee |
| timestamp | string/null | Horodatage de la detection |

**Reponse 404 :**

```json
{
  "detail": "No fraud data found for user unknown_user"
}
```

**Cle Redis** : `fraud:{user_id}` (TTL: 24h)

---

### GET /recommendations/{user_id}

Retourne les recommandations personnalisees pour un utilisateur.

**Parametres :**

| Parametre | Type | Description |
|-----------|------|-------------|
| user_id | string (path) | Identifiant utilisateur |

**Reponse 200 :**

```json
{
  "user_id": "user_1001",
  "recommendations": [
    {
      "item_id": "item_100",
      "score": 0.95,
      "category": "Electronics"
    },
    {
      "item_id": "item_200",
      "score": 0.87,
      "category": "Books"
    }
  ],
  "count": 2,
  "timestamp": "2024-01-15T10:30:00"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| user_id | string | Identifiant utilisateur |
| recommendations | array | Liste de produits recommandes |
| recommendations[].item_id | string | ID du produit |
| recommendations[].score | float (0-1) | Score de pertinence |
| recommendations[].category | string/null | Categorie du produit |
| count | int | Nombre de recommandations |
| timestamp | string/null | Horodatage |

**Cle Redis** : `reco:{user_id}` (TTL: 1h)

---

### GET /inventory/{product_id}

Retourne la prevision d'inventaire pour un produit.

**Parametres :**

| Parametre | Type | Description |
|-----------|------|-------------|
| product_id | string (path) | Identifiant produit (SKU) |

**Reponse 200 :**

```json
{
  "product_id": "SKU0001",
  "current_quantity": 250,
  "forecast_7days": [240, 230, 220, 210, 200, 190, 180],
  "needs_reorder": false,
  "alert": null,
  "timestamp": "2024-01-15T10:30:00"
}
```

**Reponse 200 (stock bas) :**

```json
{
  "product_id": "SKU0002",
  "current_quantity": 50,
  "forecast_7days": [45, 40, 35, 30, 25, 20, 15],
  "needs_reorder": true,
  "alert": "REORDER: Stock below threshold (50 < 100)",
  "timestamp": "2024-01-15T10:30:00"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| product_id | string | Identifiant produit |
| current_quantity | int | Stock actuel |
| forecast_7days | array/null | Prevision sur 7 jours |
| needs_reorder | bool | true si stock < 100 (INVENTORY_ALERT_THRESHOLD) |
| alert | string/null | Message d'alerte si reapprovisionnement necessaire |
| timestamp | string/null | Horodatage |

**Cle Redis** : `inventory:{product_id}` (TTL: 7 jours)

---

### GET /metrics

Expose les metriques au format Prometheus.

**Reponse 200 (text/plain) :**

```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{endpoint="fraud",status="200"} 42.0
api_requests_total{endpoint="recommendations",status="200"} 15.0

# HELP api_request_latency_seconds Request latency
# TYPE api_request_latency_seconds histogram
api_request_latency_seconds_bucket{endpoint="fraud",le="0.005"} 38.0
```

**Metriques exposees :**

| Metrique | Type | Labels | Description |
|----------|------|--------|-------------|
| api_requests_total | Counter | endpoint, status | Total de requetes par endpoint |
| api_request_latency_seconds | Histogram | endpoint | Latence par endpoint |

---

## Kafka Consumers

3 consumers tournent en arriere-plan (threads daemon) au demarrage de l'API :

| Consumer | Topic Kafka | Cle Redis | TTL |
|----------|-------------|-----------|-----|
| FraudConsumer | fraud-scores | fraud:{user_id} | 24h |
| RecoConsumer | recommendations | reco:{user_id} | 1h |
| InventoryConsumer | inventory-changes | inventory:{product_id} | 7 jours |

Chaque consumer :
1. Lit les messages depuis Kafka (poll loop)
2. Parse le JSON
3. Stocke dans Redis avec `SETEX` (cle + TTL)

---

## Modeles Pydantic

Fichier : `serving/api/models.py`

| Modele | Champs | Utilise par |
|--------|--------|-------------|
| FraudResponse | user_id, fraud_score, is_fraud, amount, alert, timestamp | GET /fraud |
| RecommendationItem | item_id, score, category | GET /recommendations |
| RecommendationResponse | user_id, recommendations, count, timestamp | GET /recommendations |
| InventoryResponse | product_id, current_quantity, forecast_7days, needs_reorder, alert, timestamp | GET /inventory |
| ServiceStatus | connected, latency_ms | GET /health |
| HealthResponse | status, redis, kafka, uptime | GET /health |

---

## Configuration

Toutes les constantes dans `config/constants.py` :

| Constante | Valeur | Description |
|-----------|--------|-------------|
| API_HOST | 0.0.0.0 | Adresse d'ecoute |
| API_PORT | 8000 | Port de l'API |
| FRAUD_THRESHOLD | 0.85 | Seuil de fraude |
| INVENTORY_ALERT_THRESHOLD | 100 | Seuil d'alerte stock |
| REDIS_HOST | localhost | Hote Redis |
| REDIS_PORT | 6379 | Port Redis |
| REDIS_CACHE_TTL_FRAUD | 86400 | TTL fraude (24h) |
| REDIS_CACHE_TTL_RECO | 3600 | TTL recommandations (1h) |
| REDIS_INVENTORY_TTL_SECONDS | 604800 | TTL inventaire (7j) |

Toutes surchargeable par variable d'environnement : `os.getenv("REDIS_HOST", REDIS_HOST)`

---

## Codes d'erreur

| Code | Situation |
|------|-----------|
| 200 | Succes |
| 404 | Donnee non trouvee dans Redis |
| 422 | Parametre invalide (validation Pydantic) |
| 500 | Erreur serveur |
