{#
Intermediate model: Product-level metrics.
Aggregates sales data per product for analysis and ranking.
Materialized as ephemeral.
#}

{{ config(materialized='ephemeral') }}

with order_details as (
    select * from {{ ref('int_order_details') }}
),

product_aggregates as (
    select
        product_id,
        product_sk,
        count(distinct order_id) as total_orders,
        count(*) as total_line_items,
        sum(quantity) as total_units_sold,
        sum(net_revenue) as total_revenue,
        sum(gross_revenue) as total_gross_revenue,
        sum(total_cost) as total_cost,
        sum(net_profit) as total_profit,
        avg(profit_margin_pct) as avg_profit_margin_pct,
        avg(net_revenue) as avg_revenue_per_order,
        count(distinct customer_id) as unique_customers,
        min(order_date) as first_sale_date,
        max(order_date) as last_sale_date
    from order_details
    where is_bad_data_record = 0
    group by product_id, product_sk
),

ranked as (
    select
        *,
        row_number() over (order by total_revenue desc) as revenue_rank,
        row_number() over (order by total_units_sold desc) as volume_rank,
        row_number() over (order by total_profit desc) as profit_rank,
        row_number() over (order by avg_profit_margin_pct desc) as margin_rank
    from product_aggregates
)

select * from ranked
