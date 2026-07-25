-- Singular test: Every day should have at least some sales within the data range
-- Gaps in the date spine indicate missing data or ETL issues
{{ config(severity='warn') }}

with date_range as (
    select date_actual
    from {{ ref('dim_date') }}
    where date_actual between (select min(order_date) from {{ ref('fact_sales') }})
        and (select max(order_date) from {{ ref('fact_sales') }})
),
daily_sales as (
    select order_date, count(*) as sale_count
    from {{ ref('fact_sales') }}
    group by order_date
)
select
    dr.date_actual,
    coalesce(ds.sale_count, 0) as sale_count
from date_range dr
left join daily_sales ds on dr.date_actual = ds.order_date
where ds.order_date is null
