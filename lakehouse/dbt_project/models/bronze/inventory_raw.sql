-- models/bronze/inventory_raw.sql

{{ config(
    materialized='table',
    schema='bronze',
    description='Raw inventory changes',
    tags=['bronze', 'daily']
) }}

select
    product_id,
    warehouse_id,
    quantity_change,
    current_stock,
    cast(timestamp as timestamp) as timestamp,
    current_timestamp() as ingestion_timestamp
from {{ source('kafka', 'inventory') }}
