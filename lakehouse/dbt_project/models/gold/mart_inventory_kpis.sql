-- models/gold/mart_inventory_kpis.sql
-- Daily inventory KPIs aggregation

{{ config(
    materialized='table',
    schema='gold',
    description='Daily inventory KPIs per product',
    tags=['gold', 'daily']
) }}

select
    product_id,
    cast(timestamp as date) as metric_date,
    count(*) as total_changes,
    sum(case when quantity_change > 0 then quantity_change else 0 end) as daily_stock_in,
    sum(case when quantity_change < 0 then abs(quantity_change) else 0 end) as daily_stock_out,
    min(current_stock) as min_stock,
    max(current_stock) as max_stock,
    round(avg(current_stock), 0) as avg_stock,
    sum(case when needs_reorder then 1 else 0 end) as reorder_alerts,
    case
        when min(current_stock) <= 0 then true
        else false
    end as had_stockout
from {{ ref('inventory_state') }}
group by product_id, cast(timestamp as date)
