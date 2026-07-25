-- Singular test: Catch duplicate order+line combinations
-- EXPECTED TO FAIL -- intentional bad data
{{ config(severity='error', tags=['data_quality']) }}

with dupes as (
    select
        order_id,
        line_item_id,
        count(*) as occurrence_count
    from {{ ref('stg_sales') }}
    group by order_id, line_item_id
    having count(*) > 1
)
select * from dupes
