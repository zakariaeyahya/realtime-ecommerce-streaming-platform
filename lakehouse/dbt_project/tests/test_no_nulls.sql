-- tests/test_no_nulls.sql
-- Ensure critical fields are never null

select count(*)
from {{ ref('events_clean') }}
where event_id is null
    or user_id is null
    or timestamp is null
having count(*) > 0
