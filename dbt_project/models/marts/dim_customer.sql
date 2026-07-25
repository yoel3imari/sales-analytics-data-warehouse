{#
Dimension: Customer.
SCD Type 1 attributes (overwritten on change).
Surrogate key for SCD Type 2 compatibility.
#}

{{ config(materialized='table') }}

with customers as (
    select * from {{ ref('stg_customers') }}
),

customer_metrics as (
    select * from {{ ref('int_customer_metrics') }}
)

select
    -- Surrogate key
    c.customer_sk,

    -- Natural key
    c.customer_id,

    -- Customer attributes
    c.first_name,
    c.last_name,
    c.email,
    c.phone,
    c.address_line1,
    c.address_line2,
    c.city,
    c.state,
    c.postal_code,
    c.country,

    -- Demographics
    c.birth_date,
    date_diff('year', c.birth_date, current_date) as age,
    c.gender,
    c.income_bracket,

    -- Cohort
    c.cohort,

    -- Dates
    c.signup_date,
    c.last_update_date,

    -- Enriched metrics (from intermediate)
    cm.total_orders,
    cm.total_revenue,
    cm.total_profit,
    cm.avg_order_value,
    cm.first_order_date,
    cm.last_order_date,
    cm.days_since_last_order,
    cm.value_segment,
    cm.frequency_segment,
    cm.recency_segment,
    cm.customer_tier,

    -- SCD metadata
    current_date as valid_from,
    null::date as valid_to,
    1 as is_current,

    -- Audit
    current_timestamp as dbt_loaded_at

from customers c
left join customer_metrics cm on c.customer_id = cm.customer_id
