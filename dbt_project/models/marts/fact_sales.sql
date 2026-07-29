{#
Fact: Sales transactions.
Incremental model with measures and foreign keys to dimensions.
Unique key: order_line_sk (composite of order_id + line_item_id).

Note: Bad data records (is_bad_data_record = 1) are filtered out upstream in stg_sales.sql.
#}

{{ config(
    materialized='incremental',
    unique_key='order_line_sk',
    on_schema_change='append_new_columns'
) }}

with order_details as (
    select * from {{ ref('int_order_details') }}
),

dim_customer as (
    select customer_sk, customer_id from {{ ref('dim_customer') }}
),

dim_product as (
    select product_sk, product_id from {{ ref('dim_product') }}
),

dim_date as (
    select date_sk, date_actual from {{ ref('dim_date') }}
),

joined as (
    select
        -- Surrogate keys
        od.order_line_sk,

        -- Foreign keys to dimensions
        dc.customer_sk,
        dp.product_sk,
        dd_order.date_sk as order_date_sk,
        dd_ship.date_sk as ship_date_sk,

        -- Business keys (for audit)
        od.order_id,
        od.line_item_id,
        od.customer_id,
        od.product_id,

        -- Dates
        od.order_date,
        od.ship_date,

        -- Measures
        od.quantity,
        od.unit_price,
        od.discount_amount,
        od.list_price,
        od.standard_cost,

        -- Derived measures
        od.gross_revenue,
        od.net_revenue,
        od.total_cost,
        od.gross_profit,
        od.net_profit,
        od.profit_margin_pct,

        -- Geography
        od.ship_city,
        od.ship_state,
        od.ship_country,

        -- Channel & POS Store details
        od.channel,
        od.store_id,
        od.store_name,
        od.pos_terminal_id,
        od.payment_method,
        od.is_streaming,

        -- Bad data flag
        od.is_bad_data_record,

        -- Audit
        current_timestamp as dbt_loaded_at

    from order_details od
    left join dim_customer dc on od.customer_id = dc.customer_id
    left join dim_product dp on od.product_id = dp.product_id
    left join dim_date dd_order on od.order_date = dd_order.date_actual
    left join dim_date dd_ship on od.ship_date = dd_ship.date_actual
)

select * from joined

{% if is_incremental() %}
    where order_date >= (
        select coalesce(max(order_date), '1900-01-01') from {{ this }}
    )
{% endif %}
