{#
Dimension: Product.
SCD Type 1 attributes with surrogate key.
#}

{{ config(materialized='table') }}

with products as (
    select * from {{ ref('stg_products') }}
),

product_metrics as (
    select * from {{ ref('int_product_metrics') }}
)

select
    -- Surrogate key
    p.product_sk,

    -- Natural key
    p.product_id,

    -- Product attributes
    p.product_name,
    p.category,
    p.subcategory,
    p.brand,

    -- Category hierarchy
    p.category as product_category,
    p.subcategory as product_subcategory,
    p.brand as product_brand,

    -- Pricing
    p.list_price,
    p.standard_cost,
    (p.list_price - p.standard_cost) as markup_amount,
    case
        when p.list_price > 0
        then ((p.list_price - p.standard_cost) / p.list_price) * 100
        else null
    end as markup_pct,

    -- Physical attributes
    p.color,
    p.size,
    p.weight_kg,

    -- Dates
    p.launch_date,
    p.discontinued_date,
    case
        when p.discontinued_date is not null then 'DISCONTINUED'
        else 'ACTIVE'
    end as product_status,

    -- Enriched metrics
    pm.total_units_sold,
    pm.total_revenue,
    pm.total_profit,
    pm.avg_profit_margin_pct,
    pm.revenue_rank,
    pm.volume_rank,
    pm.profit_rank,

    -- SCD metadata
    current_date as valid_from,
    null::date as valid_to,
    1 as is_current,

    -- Audit
    current_timestamp as dbt_loaded_at

from products p
left join product_metrics pm on p.product_id = pm.product_id
