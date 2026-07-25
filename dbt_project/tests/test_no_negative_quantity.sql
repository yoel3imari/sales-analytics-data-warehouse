-- Singular test: Catch negative quantity bad data
-- This test is EXPECTED TO FAIL because we intentionally injected bad data
{{ config(severity='error', tags=['data_quality']) }}

select
    order_id,
    line_item_id,
    quantity
from {{ ref('stg_sales') }}
where quantity < 0
