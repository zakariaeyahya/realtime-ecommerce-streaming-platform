-- models/silver/events_clean.sql
-- Cleaned and enriched events with deduplication

{{ config(
    materialized='table',
    schema='silver',
    description='Deduplicated and enriched events',
    tags=['silver', 'daily']
) }}

with dedup as (
    select
        event_id,
        user_id,
        event_type,
        cast(event_data as double) as event_value,
        timestamp,
        row_number() over (partition by event_id order by ingestion_timestamp desc) as rn
    from {{ ref('events_raw') }}
    where event_id is not null
)
select
    event_id,
    user_id,
    event_type,
    event_value,
    timestamp,
    current_timestamp() as dbt_created_at
from dedup
where rn = 1
