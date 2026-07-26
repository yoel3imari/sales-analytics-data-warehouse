{#
Dead-Letter Queue (DLQ) model for rejected sales records.
Captures all invalid/corrupted records (is_bad_data_record = 1) for monitoring and data auditing.
#}

with source as (
    select * from {{ source('raw', 'raw_sales') }}
),

rejected as (
    select
        -- Business keys
        trim(order_id) as order_id,
        try_cast(line_item_id as integer) as line_item_id,

        -- Composite key
        md5(
            cast(coalesce(cast(order_id as varchar), '') as varchar) ||
            '|' ||
            cast(coalesce(cast(line_item_id as varchar), '') as varchar)
        ) as order_line_sk,

        -- Foreign keys
        trim(customer_id) as customer_id,
        trim(product_id) as product_id,

        -- Date fields
        try_cast(order_date as date) as order_date,
        try_cast(ship_date as date) as ship_date,

        -- Measures
        try_cast(quantity as integer) as quantity,
        try_cast(unit_price as decimal(10,2)) as unit_price,
        try_cast(discount_amount as decimal(10,2)) as discount_amount,

        -- Error reason flags
        case when customer_id is null or trim(cast(customer_id as varchar)) = ''
            then 1 else 0 end as is_null_customer,
        case when try_cast(quantity as integer) < 0
            then 1 else 0 end as is_negative_quantity,
        case when try_cast(order_date as date) > current_date
            then 1 else 0 end as is_future_date,
        case when try_cast(unit_price as decimal(10,2)) <= 0
            then 1 else 0 end as is_zero_price,

        -- Rejection metadata
        current_timestamp as rejected_at
    from source
    where customer_id is null or trim(cast(customer_id as varchar)) = ''
       or try_cast(quantity as integer) < 0
       or try_cast(order_date as date) > current_date
       or try_cast(unit_price as decimal(10,2)) <= 0
)

select * from rejected
