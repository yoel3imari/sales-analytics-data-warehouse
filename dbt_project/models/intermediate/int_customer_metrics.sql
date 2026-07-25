{#
Intermediate model: Customer-level metrics.
Aggregates sales data per customer for segmentation and analysis.
Materialized as ephemeral.
#}

{{ config(materialized='ephemeral') }}

with order_details as (
    select * from {{ ref('int_order_details') }}
),

customer_orders as (
    select
        customer_id,
        customer_sk,
        count(distinct order_id) as total_orders,
        count(*) as total_line_items,
        sum(quantity) as total_units_purchased,
        sum(net_revenue) as total_revenue,
        sum(gross_revenue) as total_gross_revenue,
        sum(total_cost) as total_cost,
        sum(net_profit) as total_profit,
        avg(profit_margin_pct) as avg_profit_margin_pct,
        avg(net_revenue) as avg_order_value,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date,
        count(distinct product_id) as distinct_products_purchased,
        count(distinct date_trunc('month', order_date)) as active_months
    from order_details
    where is_bad_data_record = 0
    group by customer_id, customer_sk
),

segmented as (
    select
        *,
        -- Customer segmentation
        case
            when total_revenue >= 5000 then 'HIGH_VALUE'
            when total_revenue >= 2000 then 'MID_VALUE'
            else 'LOW_VALUE'
        end as value_segment,

        case
            when total_orders >= 20 then 'FREQUENT_BUYER'
            when total_orders >= 5 then 'REGULAR_BUYER'
            when total_orders >= 1 then 'OCCASIONAL_BUYER'
            else 'NEW_BUYER'
        end as frequency_segment,

        -- Days since last order (null if no orders)
        case
            when last_order_date is not null
            then datediff('day', last_order_date, current_date)
            else null
        end as days_since_last_order,

        -- Recency segment
        case
            when last_order_date is null then 'NEW'
            when datediff('day', last_order_date, current_date) <= 30 then 'ACTIVE'
            when datediff('day', last_order_date, current_date) <= 90 then 'RECENT'
            when datediff('day', last_order_date, current_date) <= 180 then 'LAPSED'
            else 'CHURNED'
        end as recency_segment,

        -- Composite segment (for analysis)
        case
            when total_revenue >= 5000 and total_orders >= 20 then 'PLATINUM'
            when total_revenue >= 2000 and total_orders >= 10 then 'GOLD'
            when total_revenue >= 500 then 'SILVER'
            else 'BRONZE'
        end as customer_tier

    from customer_orders
)

select * from segmented
