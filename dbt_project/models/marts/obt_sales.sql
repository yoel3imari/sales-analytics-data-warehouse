{#
One Big Table: Denormalized sales for BI consumption.
Joins fact_sales + ALL dimension attributes so Metabase can query
a single table without joins.

Materialized as table (full refresh) — small enough for DuckDB.
#}

{{ config(materialized='table') }}

with fact as (
    select * from {{ ref('fact_sales') }}
),

customer as (
    select * from {{ ref('dim_customer') }}
),

product as (
    select * from {{ ref('dim_product') }}
),

order_date as (
    select * from {{ ref('dim_date') }}
),

ship_date as (
    select * from {{ ref('dim_date') }}
),

joined as (
    select
        -- ── Fact measures ──
        fact.order_line_sk,
        fact.order_id,
        fact.line_item_id,
        fact.order_date,
        fact.ship_date,
        fact.quantity,
        fact.unit_price,
        fact.discount_amount,
        fact.list_price,
        fact.standard_cost,
        fact.gross_revenue,
        fact.net_revenue,
        fact.total_cost,
        fact.gross_profit,
        fact.net_profit,
        fact.profit_margin_pct,
        fact.channel,

        -- ── Customer attributes ──
        cust.customer_id,
        cust.first_name,
        cust.last_name,
        cust.email,
        cust.city as customer_city,
        cust.state as customer_state,
        cust.postal_code as customer_postal_code,
        cust.country as customer_country,
        cust.gender,
        cust.income_bracket,
        cust.cohort,
        cust.age,
        cust.signup_date,
        cust.value_segment,
        cust.frequency_segment,
        cust.recency_segment,
        cust.customer_tier,
        cust.total_orders as customer_total_orders,
        cust.total_revenue as customer_total_revenue,

        -- ── Product attributes ──
        prod.product_id,
        prod.product_name,
        prod.category,
        prod.subcategory,
        prod.brand,
        prod.product_category,
        prod.product_subcategory,
        prod.product_brand,
        prod.color,
        prod.size,
        prod.list_price as product_list_price,
        prod.standard_cost as product_standard_cost,
        prod.product_status,
        prod.revenue_rank,
        prod.volume_rank,

        -- ── Order Date attributes ──
        od.year as order_year,
        od.quarter as order_quarter,
        od.quarter_label as order_quarter_label,
        od.month as order_month,
        od.month_name as order_month_name,
        od.week_of_year as order_week_of_year,
        od.day_of_month as order_day_of_month,
        od.day_of_week as order_day_of_week,
        od.day_name as order_day_name,
        od.is_weekend as order_is_weekend,
        od.season as order_season,
        od.is_holiday as order_is_holiday,
        od.holiday_name as order_holiday_name,

        -- ── Ship Date attributes ──
        sd.year as ship_year,
        sd.month as ship_month,
        sd.month_name as ship_month_name,
        sd.day_of_week as ship_day_of_week,
        sd.day_name as ship_day_name

    from fact
    left join customer cust on fact.customer_sk = cust.customer_sk
    left join product prod on fact.product_sk = prod.product_sk
    left join order_date od on fact.order_date_sk = od.date_sk
    left join ship_date sd on fact.ship_date_sk = sd.date_sk
)

select * from joined
