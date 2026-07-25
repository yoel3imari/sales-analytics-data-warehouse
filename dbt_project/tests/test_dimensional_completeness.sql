-- Singular test: All FK values in fact table exist in dimension tables
-- Referential integrity check across all dimension references
{{ config(severity='warn') }}

with missing_customers as (
    select distinct fact.customer_sk
    from {{ ref('fact_sales') }} fact
    left join {{ ref('dim_customer') }} dim on fact.customer_sk = dim.customer_sk
    where dim.customer_sk is null
),
missing_products as (
    select distinct fact.product_sk
    from {{ ref('fact_sales') }} fact
    left join {{ ref('dim_product') }} dim on fact.product_sk = dim.product_sk
    where dim.product_sk is null
)
select 'missing_customer_sk' as check_type, customer_sk as missing_key from missing_customers
union all
select 'missing_product_sk' as check_type, product_sk as missing_key from missing_products
