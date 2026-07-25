{#
Snapshot: Customer SCD Type 2.
Tracks changes to customer attributes over time using check strategy.
Natural key: customer_id
Check cols: all mutable attributes
Target schema: snapshots
#}

{% snapshot snap_customers %}

{{
    config(
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='check',
        check_cols=[
            'first_name',
            'last_name',
            'email',
            'phone',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'postal_code',
            'country',
            'income_bracket',
            'cohort'
        ],
        invalidate_hard_deletes=False,
    )
}}

select
    -- Natural key
    customer_id,

    -- Customer attributes
    first_name,
    last_name,
    email,
    phone,
    address_line1,
    address_line2,
    city,
    state,
    postal_code,
    country,
    birth_date,
    gender,
    income_bracket,
    cohort,
    signup_date,
    last_update_date

from {{ ref('stg_customers') }}

{% endsnapshot %}
