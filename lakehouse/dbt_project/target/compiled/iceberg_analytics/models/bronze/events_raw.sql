-- models/bronze/events_raw.sql
-- Raw events from Kafka - minimal transformation



select
    event_id,
    user_id,
    event_type,
    cast(timestamp as timestamp) as timestamp,
    event_data,
    current_timestamp() as ingestion_timestamp
from default.events
where timestamp >= '2024-01-01'