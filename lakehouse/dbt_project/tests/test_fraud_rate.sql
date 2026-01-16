-- tests/test_fraud_rate.sql
-- Fraud rate should not exceed 5%

select count(*)
from (
    select cast(timestamp as date) as fraud_date,
           round(sum(case when is_fraud then 1 else 0 end)::float / count(*) * 100, 2) as fraud_rate
    from {{ ref('fraud_events') }}
    group by 1
)
where fraud_rate > 5
