-- models/bronze/fraud_raw.sql



select
    event_id,
    user_id,
    fraud_score,
    is_fraud,
    cast(timestamp as timestamp) as timestamp,
    current_timestamp() as ingestion_timestamp
from default.fraud_scores