-- Singular test: Catch future date bad data
-- EXPECTED TO FAIL -- intentional bad data
{{ config(severity='error', tags=['data_quality']) }}

select
    order_id,
    order_date
from {{ ref('stg_sales') }}
where order_date > current_date
