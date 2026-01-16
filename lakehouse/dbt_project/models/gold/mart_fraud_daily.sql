-- models/gold/mart_fraud_daily.sql
-- Daily fraud metrics aggregation

{{ config(
    materialized='table',
    schema='gold',
    description='Daily fraud metrics',
    tags=['gold', 'daily']
) }}

select
    cast(timestamp as date) as metric_date,
    count(*) as total_transactions,
    sum(case when is_fraud then 1 else 0 end) as fraud_count,
    round(sum(case when is_fraud then 1 else 0 end)::float / count(*) * 100, 2) as fraud_rate,
    sum(case when is_fraud then amount else 0 end) as total_fraud_amount,
    avg(fraud_score) as avg_fraud_score
from {{ ref('fraud_events') }}
group by 1
