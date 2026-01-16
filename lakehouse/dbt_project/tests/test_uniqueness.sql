-- tests/test_uniqueness.sql
-- Event IDs must be unique

select event_id, count(*) as cnt
from {{ ref('events_clean') }}
group by event_id
having count(*) > 1
