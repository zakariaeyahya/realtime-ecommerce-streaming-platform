# Guide - Lakehouse (Iceberg + dbt)

## Vue d'ensemble

![Lakehouse Architecture](diagrams/lakehouse.png)

Le lakehouse utilise Apache Iceberg comme format de table et dbt pour les transformations SQL, avec MinIO comme stockage S3-compatible.

## Architecture Bronze/Silver/Gold

### Bronze (Donnees brutes)

Donnees brutes ingerees depuis Kafka, sans transformation.

| Modele | Source Kafka | Description |
|--------|-------------|-------------|
| events_raw | ecommerce-events | Tous les evenements (view, addtocart, transaction) |
| fraud_raw | fraud-scores | Scores de fraude bruts |
| inventory_raw | inventory-changes | Variations de stock brutes |

### Silver (Donnees nettoyees)

Donnees deduplicees, enrichies et nettoyees.

| Modele | Source | Transformations |
|--------|--------|-----------------|
| fraud_scored | fraud_raw | Classification (high/medium/low risk), enrichissement |
| user_sessions | events_raw | Sessions utilisateur, agregations par session |
| inventory_state | inventory_raw | Deduplication, calcul stock agrege, flag reorder |

### Gold (Dimensions et KPIs)

Modeles analytiques prets pour le reporting.

| Modele | Sources | Description |
|--------|---------|-------------|
| dim_users | fraud_scored, user_sessions | Dimension utilisateur (segments VIP/Regular/Browser, AOV, activite) |
| dim_products | fraud_scored, user_sessions | Dimension produit (stats evenements, stock, taux conversion) |
| mart_inventory_kpis | inventory_state | KPIs inventaire quotidiens (ruptures, rotation, reapprovisionnements) |

## Fichiers dbt

```
lakehouse/dbt_project/
|-- dbt_project.yml          # Configuration projet
|-- models/
|   |-- schema.yml           # Declaration des modeles et sources
|   |-- bronze/
|   |   |-- events_raw.sql
|   |   |-- fraud_raw.sql
|   |   +-- inventory_raw.sql
|   |-- silver/
|   |   |-- fraud_scored.sql
|   |   |-- user_sessions.sql
|   |   +-- inventory_state.sql
|   +-- gold/
|       |-- dim_users.sql
|       |-- dim_products.sql
|       +-- mart_inventory_kpis.sql
+-- tests/
    +-- test_data_freshness.sql
```

## Technologies

| Composant | Role |
|-----------|------|
| Apache Iceberg | Format de table (ACID, time travel, schema evolution) |
| dbt | Transformations SQL (Bronze > Silver > Gold) |
| MinIO | Stockage S3-compatible (port 9010 API, port 9001 console) |
| Spark SQL | Moteur de requetes sur les tables Iceberg |

## Spark Jobs

### kafka_to_bronze (`lakehouse/spark_jobs/kafka_to_bronze.py`)

Job Spark Structured Streaming qui lit les topics Kafka et ecrit dans les tables Iceberg Bronze.

### Configuration Iceberg

- Catalogue : `lakehouse/iceberg_setup/init_catalog.py`
- Tables : `lakehouse/iceberg_setup/init_tables.py`

## Test de qualite

Le fichier `tests/test_data_freshness.sql` verifie que les donnees Bronze ont moins de 24 heures :

```sql
SELECT COUNT(*) as stale_count
FROM {{ source('kafka', 'ecommerce_events') }}
WHERE timestamp < UNIX_TIMESTAMP() - 86400
HAVING COUNT(*) > (SELECT COUNT(*) * 0.5 FROM {{ source('kafka', 'ecommerce_events') }})
```

## Commandes dbt

```bash
# Compiler les modeles (verification syntaxe)
dbt compile --project-dir lakehouse/dbt_project --profiles-dir lakehouse/dbt_project

# Executer les modeles
dbt run --project-dir lakehouse/dbt_project --profiles-dir lakehouse/dbt_project

# Lancer les tests
dbt test --project-dir lakehouse/dbt_project --profiles-dir lakehouse/dbt_project
```

## Statut

Le lakehouse est partiellement implemente :
- Les modeles dbt sont ecrits et compilent
- L'execution necessite un cluster Spark avec le connecteur Iceberg
- MinIO est configure et operationnel dans Docker
