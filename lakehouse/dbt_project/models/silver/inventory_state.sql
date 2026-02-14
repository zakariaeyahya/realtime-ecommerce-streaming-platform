-- models/silver/inventory_state.sql
-- Current and historical inventory state per product/warehouse

{{ config(
    materialized='table',
    schema='silver',
    description='Deduplicated inventory state with current stock levels',
    tags=['silver', 'daily']
) }}

with dedup as (
    select
        product_id,
        warehouse_id,
        quantity_change,
        current_stock,
        timestamp,
        row_number() over (
            partition by product_id, warehouse_id, timestamp
            order by ingestion_timestamp desc
        ) as rn
    from {{ ref('inventory_raw') }}
    where product_id is not null
),

cleaned as (
    select
        product_id,
        warehouse_id,
        quantity_change,
        current_stock,
        timestamp
    from dedup
    where rn = 1
),

inventory_agg as (
    select
        product_id,
        warehouse_id,
        min(current_stock) as min_stock,
        max(current_stock) as max_stock,
        avg(current_stock) as avg_stock,
        sum(case when quantity_change > 0 then quantity_change else 0 end) as total_stock_in,
        sum(case when quantity_change < 0 then abs(quantity_change) else 0 end) as total_stock_out,
        count(*) as total_changes,
        max(timestamp) as last_update,
        max(current_stock) as latest_stock
    from cleaned
    group by product_id, warehouse_id
)

select
    c.product_id,
    c.warehouse_id,
    c.quantity_change,
    c.current_stock,
    c.timestamp,
    a.min_stock,
    a.max_stock,
    a.avg_stock,
    a.total_stock_in,
    a.total_stock_out,
    a.total_changes,
    case when c.current_stock < 100 then true else false end as needs_reorder,
    current_timestamp() as dbt_created_at
from cleaned c
left join inventory_agg a
    on c.product_id = a.product_id
    and c.warehouse_id = a.warehouse_id
