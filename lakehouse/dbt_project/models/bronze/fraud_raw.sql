-- models/bronze/fraud_raw.sql

{{ config(
    materialized='table',
    schema='bronze',
    description='Raw fraud scores from Flink job',
    tags=['bronze', 'daily']
) }}

select
    event_id,
    user_id,
    fraud_score,
    is_fraud,
    cast(timestamp as timestamp) as timestamp,
    current_timestamp() as ingestion_timestamp
from {{ source('kafka', 'fraud_scores') }}
