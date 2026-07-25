-- Singular test: Ensure no null customer foreign keys in fact table
-- Fact table should only reference valid customer dimension records
{{ config(severity='warn') }}

select
    fact.order_line_sk,
    fact.order_id
from {{ ref('fact_sales') }} fact
left join {{ ref('dim_customer') }} cust on fact.customer_sk = cust.customer_sk
where cust.customer_sk is null
