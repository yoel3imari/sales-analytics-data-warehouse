-- Singular test: No overlapping validity periods in SCD2 snapshots
-- Each customer's validity intervals should be sequential and non-overlapping
{{ config(severity='warn') }}

with validity_check as (
    select
        customer_id,
        dbt_valid_from,
        dbt_valid_to,
        lag(dbt_valid_from) over (
            partition by customer_id
            order by dbt_valid_from
        ) as prev_valid_from
    from {{ ref('snap_customers') }}
)
select
    customer_id,
    dbt_valid_from,
    dbt_valid_to,
    prev_valid_from
from validity_check
where prev_valid_from is not null
    and dbt_valid_from < prev_valid_from
