{#
Intermediate model: Order details.
Joins stg_sales + stg_products + stg_customers to compute derived measures.
Materialized as ephemeral (compiled as CTE into downstream models).
#}

{{ config(materialized='ephemeral') }}

with sales as (
    select * from {{ ref('stg_sales') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

joined as (
    select
        -- Surrogate keys
        s.order_line_sk,
        s.customer_id,
        s.product_id,
        c.customer_sk,
        p.product_sk,

        -- Order identifiers
        s.order_id,
        s.line_item_id,

        -- Dates
        s.order_date,
        s.ship_date,

        -- Measures
        s.quantity,
        s.unit_price,
        s.discount_amount,
        p.list_price,
        p.standard_cost,

        -- Derived measures
        s.quantity * s.unit_price as gross_revenue,
        s.quantity * (s.unit_price - s.discount_amount) as net_revenue,
        s.quantity * p.standard_cost as total_cost,
        (s.quantity * s.unit_price) - (s.quantity * p.standard_cost) as gross_profit,
        (s.quantity * (s.unit_price - s.discount_amount)) - (s.quantity * p.standard_cost) as net_profit,
        case
            when (s.quantity * s.unit_price) > 0
            then ((s.quantity * (s.unit_price - s.discount_amount)) - (s.quantity * p.standard_cost))
                 / nullif((s.quantity * s.unit_price), 0) * 100
            else null
        end as profit_margin_pct,

        -- Geography
        s.ship_city,
        s.ship_state,
        s.ship_country,

        -- Channel & POS Store details
        s.channel,
        s.store_id,
        s.store_name,
        s.pos_terminal_id,
        s.payment_method,
        s.is_streaming,

        -- Bad data flag
        s.is_bad_data_record

    from sales s
    left join products p on s.product_id = p.product_id
    left join customers c on s.customer_id = c.customer_id
)

select * from joined
