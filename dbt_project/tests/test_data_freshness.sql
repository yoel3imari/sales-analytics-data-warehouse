-- Singular test: Raw data should not be too old
-- Alerts when source data hasn't been updated recently
{{ config(severity='warn') }}

with max_dates as (
    select 'raw_customers' as source, max(signup_date) as max_date
    from {{ source('raw', 'raw_customers') }}
    union all
    select 'raw_products', max(launch_date)
    from {{ source('raw', 'raw_products') }}
    union all
    select 'raw_sales', max(order_date::date)
    from {{ source('raw', 'raw_sales') }}
)
select
    source,
    max_date,
    current_date as today,
    current_date - max_date as days_old
from max_dates
where max_date < current_date - 30
