-- models/bronze/inventory_raw.sql



select
    product_id,
    warehouse_id,
    quantity_change,
    current_stock,
    cast(timestamp as timestamp) as timestamp,
    current_timestamp() as ingestion_timestamp
from default.inventory