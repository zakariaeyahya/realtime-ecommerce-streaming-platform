-- models/bronze/events_raw.sql
-- Raw events from Kafka - minimal transformation

{{ config(
    materialized='table',
    schema='bronze',
    description='Raw events from Kafka topics',
    tags=['bronze', 'daily']
) }}

select
    event_id,
    user_id,
    event_type,
    cast(timestamp as timestamp) as timestamp,
    event_data,
    current_timestamp() as ingestion_timestamp
from {{ source('kafka', 'events') }}
where timestamp >= '{{ var("start_date", "2024-01-01") }}'
