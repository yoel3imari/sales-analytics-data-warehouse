{#
Snapshot: Product SCD Type 2.
Tracks changes to product attributes over time.
Natural key: product_id
Check cols: price, cost, and status attributes that can change.
#}

{% snapshot snap_products %}

{{
    config(
        target_schema='snapshots',
        unique_key='product_id',
        strategy='check',
        check_cols=[
            'product_name',
            'category',
            'subcategory',
            'list_price',
            'standard_cost',
            'color',
            'discontinued_date'
        ],
        invalidate_hard_deletes=False,
    )
}}

select
    -- Natural key
    product_id,

    -- Product attributes
    product_name,
    category,
    subcategory,
    brand,
    list_price,
    standard_cost,
    color,
    size,
    weight_kg,
    launch_date,
    discontinued_date

from {{ ref('stg_products') }}

{% endsnapshot %}
