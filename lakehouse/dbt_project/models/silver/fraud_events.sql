-- models/silver/fraud_events.sql
-- Enriched fraud detection events

{{ config(
    materialized='table',
    schema='silver',
    description='Enriched fraud detection events',
    tags=['silver', 'daily']
) }}

select
    f.event_id,
    f.user_id,
    f.fraud_score,
    f.is_fraud,
    e.event_value as amount,
    f.timestamp
from {{ ref('fraud_raw') }} f
left join {{ ref('events_raw') }} e on f.event_id = e.event_id
