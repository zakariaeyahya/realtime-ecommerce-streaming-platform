-- models/gold/fact_purchases.sql
-- Fact table: all purchase transactions

{{ config(
    materialized='table',
    schema='gold',
    description='Fact table: all purchase transactions',
    tags=['gold', 'daily'],
    partition_by={
        "field": "transaction_date",
        "data_type": "date",
        "granularity": "day"
    }
) }}

select
    event_id as transaction_id,
    user_id,
    event_type as product_id,
    event_value as amount,
    1 as quantity,
    cast(timestamp as date) as transaction_date,
    cast(current_timestamp() as timestamp) as created_at
from {{ ref('events_clean') }}
where event_type = 'purchase'
