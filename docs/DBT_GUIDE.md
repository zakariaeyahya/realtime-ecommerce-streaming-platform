# Guide - dbt (Data Build Tool)

## Vue d'ensemble

dbt transforme les donnees brutes (Bronze) en modeles analytiques (Gold) via des requetes SQL organisees en 3 couches.

## Structure du projet dbt

```
lakehouse/dbt_project/
|-- dbt_project.yml          # Nom: streaming_analytics, version: 1.0.0
|-- profiles.yml             # Connexion Spark Thrift Server
|-- models/
|   |-- schema.yml           # Sources Kafka + declarations modeles
|   |-- bronze/              # Donnees brutes
|   |-- silver/              # Donnees nettoyees
|   +-- gold/                # KPIs et dimensions
+-- tests/
    +-- test_data_freshness.sql
```

## Sources

Definies dans `models/schema.yml` :

| Source | Table | Description |
|--------|-------|-------------|
| kafka | ecommerce_events | Evenements bruts |
| kafka | fraud_scores | Scores de fraude |
| kafka | inventory_changes | Variations de stock |

## Modeles Bronze

### events_raw.sql

```sql
SELECT
    event_id, event_type, timestamp, user_id,
    item_id, category, price, quantity
FROM {{ source('kafka', 'ecommerce_events') }}
```

Lecture directe des evenements Kafka sans transformation.

### fraud_raw.sql

```sql
SELECT
    user_id, fraud_score, amount, timestamp,
    is_fraud
FROM {{ source('kafka', 'fraud_scores') }}
```

### inventory_raw.sql

```sql
SELECT
    product_id, current_stock, warehouse_id,
    timestamp, change_type
FROM {{ source('kafka', 'inventory_changes') }}
```

## Modeles Silver

### fraud_scored.sql

Enrichit les scores de fraude avec une classification :
- **high_risk** : score >= 0.85
- **medium_risk** : score >= 0.5
- **low_risk** : score < 0.5

### user_sessions.sql

Agregations par session utilisateur :
- Nombre d'evenements par type
- Montant total et moyen
- Duree de session
- Categories visitees

### inventory_state.sql

Deduplication et agregation du stock :
- Stock agrege par produit et entrepot
- Flag `needs_reorder` (stock < 100)
- Dernier timestamp de mise a jour

## Modeles Gold

### dim_users.sql

Dimension utilisateur avec segmentation :

| Segment | Critere |
|---------|---------|
| VIP | Nombre de transactions >= 10 |
| Regular | Nombre de transactions >= 3 |
| Browser | Nombre de transactions < 3 |

Champs : user_id, segment, total_transactions, total_spent, avg_order_value, first_seen, last_seen

### dim_products.sql

Dimension produit avec statistiques :
- Nombre de vues, ajouts panier, transactions
- Taux de conversion (transactions / vues)
- Stock actuel et flag reorder
- Categorie

### mart_inventory_kpis.sql

KPIs inventaire quotidiens par produit :
- Stock moyen, min, max
- Nombre de changements
- Nombre de ruptures (stock = 0)
- Rotation du stock

## Profil de connexion

```yaml
# profiles.yml
streaming_analytics:
  target: dev
  outputs:
    dev:
      type: spark
      method: thrift
      host: localhost
      port: 10000
      schema: streaming_db
```

## Commandes

```bash
# Verifier la syntaxe
dbt compile --project-dir lakehouse/dbt_project --profiles-dir lakehouse/dbt_project

# Executer tous les modeles
dbt run --project-dir lakehouse/dbt_project --profiles-dir lakehouse/dbt_project

# Executer un modele specifique
dbt run --select dim_users --project-dir lakehouse/dbt_project

# Tests de qualite
dbt test --project-dir lakehouse/dbt_project --profiles-dir lakehouse/dbt_project
```

## Lineage (dependances)

```
Sources Kafka
    |
    v
Bronze (events_raw, fraud_raw, inventory_raw)
    |
    v
Silver (fraud_scored, user_sessions, inventory_state)
    |
    v
Gold (dim_users, dim_products, mart_inventory_kpis)
    |
    v
MinIO S3 (tables Iceberg)
```
