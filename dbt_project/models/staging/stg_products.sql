{#
Staging model for raw product data.
Standardizes column names, casts data types.
#}

with source as (
    select * from {{ source('raw', 'raw_products') }}
),

renamed as (
    select
        -- Surrogate key (DuckDB built-in md5)
        md5(cast(coalesce(cast(product_id as varchar), '') as varchar)) as product_sk,

        -- Natural key
        product_id,

        -- Product attributes
        trim(product_name) as product_name,
        trim(category) as category,
        trim(subcategory) as subcategory,
        trim(brand) as brand,

        -- Pricing
        try_cast(list_price as decimal(10,2)) as list_price,
        try_cast(standard_cost as decimal(10,2)) as standard_cost,

        -- Physical attributes
        trim(color) as color,
        trim(size) as size,
        try_cast(weight_kg as decimal(8,2)) as weight_kg,

        -- Dates
        try_cast(launch_date as date) as launch_date,
        try_cast(discontinued_date as date) as discontinued_date,

        -- Metadata
        current_timestamp as dbt_loaded_at
    from source
    where product_id is not null
        and trim(product_id) != ''
)

select * from renamed
