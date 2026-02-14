-- models/gold/dim_users.sql
-- Dimension table: users with SCD2 attributes

{{ config(
    materialized='table',
    schema='gold',
    description='User dimension table with activity summary',
    tags=['gold', 'daily']
) }}

select
    user_id,
    min(timestamp) as first_seen,
    max(timestamp) as last_seen,
    count(*) as total_events,
    sum(case when event_type = 'view' then 1 else 0 end) as total_views,
    sum(case when event_type = 'addtocart' then 1 else 0 end) as total_addtocarts,
    sum(case when event_type = 'purchase' then 1 else 0 end) as total_purchases,
    sum(case when event_type = 'search' then 1 else 0 end) as total_searches,
    coalesce(sum(event_value), 0) as total_spent,
    case
        when sum(case when event_type = 'purchase' then 1 else 0 end) > 0
        then round(
            sum(case when event_type = 'purchase' then event_value else 0 end)
            / sum(case when event_type = 'purchase' then 1 else 0 end), 2
        )
        else 0
    end as avg_order_value,
    case
        when count(*) = 0 then 'inactive'
        when sum(case when event_type = 'purchase' then 1 else 0 end) >= 10 then 'vip'
        when sum(case when event_type = 'purchase' then 1 else 0 end) >= 3 then 'regular'
        when sum(case when event_type = 'purchase' then 1 else 0 end) >= 1 then 'occasional'
        else 'browser'
    end as user_segment,
    current_timestamp() as dbt_created_at
from {{ ref('events_clean') }}
where user_id is not null
group by user_id
