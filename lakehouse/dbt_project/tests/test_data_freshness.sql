-- tests/test_data_freshness.sql
-- Verify that Bronze layer data is not older than 24 hours

select count(*)
from {{ ref('events_raw') }}
where ingestion_timestamp < current_timestamp() - interval 24 hour
  and ingestion_timestamp = (select max(ingestion_timestamp) from {{ ref('events_raw') }})
having count(*) > 0
