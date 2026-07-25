-- Singular test: Catch zero-price bad data
-- EXPECTED TO FAIL -- intentional bad data
{{ config(severity='error', tags=['data_quality']) }}

select
    order_id,
    line_item_id,
    unit_price
from {{ ref('stg_sales') }}
where unit_price <= 0
