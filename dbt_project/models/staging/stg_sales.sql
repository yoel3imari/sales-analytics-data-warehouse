{#
Staging model for clean sales data.
Unions static batch sales (raw_sales) and real-time streaming POS sales (raw_sales_stream).
Standardizes column names, filters out bad data records (is_bad_data_record = 0),
and deduplicates order line combinations.
#}

with source_batch as (
    select
        order_id,
        line_item_id,
        customer_id,
        product_id,
        order_date,
        ship_date,
        quantity,
        unit_price,
        discount_amount,
        ship_city,
        ship_state,
        ship_country,
        channel,
        cast(null as varchar) as store_id,
        cast(null as varchar) as store_name,
        cast(null as varchar) as pos_terminal_id,
        cast(null as varchar) as payment_method,
        0 as is_streaming
    from {{ source('raw', 'raw_sales') }}
),

source_stream as (
    select
        order_id,
        line_item_id,
        customer_id,
        product_id,
        order_date,
        ship_date,
        quantity,
        unit_price,
        discount_amount,
        ship_city,
        ship_state,
        ship_country,
        channel,
        store_id,
        store_name,
        pos_terminal_id,
        payment_method,
        1 as is_streaming
    from {{ source('raw', 'raw_sales_stream') }}
),

unomated as (
    select * from source_batch
    union all
    select * from source_stream
),

renamed as (
    select
        -- Business keys
        trim(cast(order_id as varchar)) as order_id,
        try_cast(line_item_id as integer) as line_item_id,

        -- Composite key for incremental fact (DuckDB built-in md5)
        md5(
            cast(coalesce(cast(order_id as varchar), '') as varchar) ||
            '|' ||
            cast(coalesce(cast(line_item_id as varchar), '') as varchar)
        ) as order_line_sk,

        -- Foreign keys
        trim(cast(customer_id as varchar)) as customer_id,
        trim(cast(product_id as varchar)) as product_id,

        -- Date fields
        try_cast(order_date as date) as order_date,
        try_cast(ship_date as date) as ship_date,

        -- Measures
        try_cast(quantity as integer) as quantity,
        try_cast(unit_price as decimal(10,2)) as unit_price,
        try_cast(discount_amount as decimal(10,2)) as discount_amount,

        -- Geography
        trim(cast(ship_city as varchar)) as ship_city,
        upper(trim(cast(ship_state as varchar))) as ship_state,
        upper(trim(cast(ship_country as varchar))) as ship_country,

        -- Channel & POS Details
        trim(cast(channel as varchar)) as channel,
        trim(cast(store_id as varchar)) as store_id,
        trim(cast(store_name as varchar)) as store_name,
        trim(cast(pos_terminal_id as varchar)) as pos_terminal_id,
        trim(cast(payment_method as varchar)) as payment_method,
        is_streaming,

        -- Bad data flags
        case when customer_id is null or trim(cast(customer_id as varchar)) = ''
            then 1 else 0 end as is_null_customer,
        case when order_id is null or trim(cast(order_id as varchar)) = '' or line_item_id is null
            then 1 else 0 end as is_null_order_key,
        case when try_cast(quantity as integer) < 0
            then 1 else 0 end as is_negative_quantity,
        case when try_cast(order_date as date) > current_date
            then 1 else 0 end as is_future_date,
        case when try_cast(unit_price as decimal(10,2)) <= 0
            then 1 else 0 end as is_zero_price,

        -- Composite bad data flag
        case when customer_id is null or trim(cast(customer_id as varchar)) = ''
               or order_id is null or trim(cast(order_id as varchar)) = '' or line_item_id is null
               or try_cast(quantity as integer) < 0
               or try_cast(order_date as date) > current_date
               or try_cast(unit_price as decimal(10,2)) <= 0
            then 1 else 0 end as is_bad_data_record,

        -- Metadata
        current_timestamp as dbt_loaded_at
    from unomated
)

select * from renamed
where is_bad_data_record = 0
qualify row_number() over (partition by order_id, line_item_id order by order_date desc) = 1
