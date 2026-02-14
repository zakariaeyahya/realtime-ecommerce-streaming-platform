-- models/gold/dim_products.sql
-- Dimension table: products with activity and stock summary

{{ config(
    materialized='table',
    schema='gold',
    description='Product dimension table with event stats and stock info',
    tags=['gold', 'daily']
) }}

with event_stats as (
    select
        event_type as product_id,
        count(*) as total_events,
        sum(case when event_type = 'view' then 1 else 0 end) as total_views,
        sum(case when event_type = 'addtocart' then 1 else 0 end) as total_addtocarts,
        sum(case when event_type = 'purchase' then 1 else 0 end) as total_purchases,
        coalesce(sum(event_value), 0) as total_revenue,
        count(distinct user_id) as unique_users,
        min(timestamp) as first_seen,
        max(timestamp) as last_seen
    from {{ ref('events_clean') }}
    where event_type is not null
    group by event_type
),

stock_stats as (
    select
        product_id,
        max(current_stock) as latest_stock,
        avg(avg_stock) as avg_stock_level,
        max(needs_reorder) as needs_reorder,
        sum(total_stock_in) as total_received,
        sum(total_stock_out) as total_sold_stock
    from {{ ref('inventory_state') }}
    group by product_id
)

select
    e.product_id,
    e.total_events,
    e.total_views,
    e.total_addtocarts,
    e.total_purchases,
    e.total_revenue,
    e.unique_users,
    case
        when e.total_views > 0
        then round(e.total_purchases::float / e.total_views * 100, 2)
        else 0
    end as conversion_rate,
    e.first_seen,
    e.last_seen,
    coalesce(s.latest_stock, 0) as latest_stock,
    coalesce(s.avg_stock_level, 0) as avg_stock_level,
    coalesce(s.needs_reorder, false) as needs_reorder,
    current_timestamp() as dbt_created_at
from event_stats e
left join stock_stats s on e.product_id = s.product_id
