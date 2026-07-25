{#
Staging model for raw customer data.
Standardizes column names, casts data types, and generates surrogate key.
#}

with source as (
    select * from {{ source('raw', 'raw_customers') }}
),

renamed as (
    select
        -- Surrogate key for SCD Type 2 (using DuckDB built-in md5 instead of dbt_utils)
        md5(cast(coalesce(cast(customer_id as varchar), '') as varchar)) as customer_sk,

        -- Natural key
        customer_id,

        -- Customer attributes
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        lower(trim(email)) as email,
        phone,
        trim(address_line1) as address_line1,
        trim(address_line2) as address_line2,
        trim(city) as city,
        upper(trim(state)) as state,
        trim(postal_code) as postal_code,
        upper(trim(country)) as country,

        -- Demographics
        try_cast(birth_date as date) as birth_date,
        upper(trim(gender)) as gender,
        upper(trim(income_bracket)) as income_bracket,

        -- Cohort
        upper(trim(cohort)) as cohort,

        -- Dates
        try_cast(signup_date as date) as signup_date,
        try_cast(last_update_date as date) as last_update_date,

        -- Metadata
        current_timestamp as dbt_loaded_at
    from source
    where customer_id is not null
        and trim(customer_id) != ''
)

select * from renamed
