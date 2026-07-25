{#
Dimension: Date.
Static date spine from 2022-01-01 to 2026-12-31 with date attributes.
Useful for time-based analysis in BI tools.
#}

{{ config(materialized='table') }}

with date_spine as (
    select
        unnest(
            generate_series(
                date '2022-01-01',
                date '2026-12-31',
                interval '1 day'
            )
        ) as date_actual
),

date_dim as (
    select
        -- Key (use integer YYYYMMDD format for BI compatibility)
        cast(strftime(date_actual, '%Y%m%d') as integer) as date_sk,

        -- Date
        date_actual as date_actual,

        -- Year attributes
        date_part('year', date_actual) as year,
        date_part('quarter', date_actual) as quarter,
        'Q' || date_part('quarter', date_actual) as quarter_label,

        -- Month attributes
        date_part('month', date_actual) as month,
        strftime(date_actual, '%B') as month_name,
        strftime(date_actual, '%b') as month_name_short,
        date_part('month', date_actual) as month_of_year,

        -- Week attributes
        date_part('week', date_actual) as week_of_year,
        date_part('day', date_actual) as day_of_month,

        -- Day attributes
        date_part('dow', date_actual) as day_of_week,
        strftime(date_actual, '%A') as day_name,
        strftime(date_actual, '%a') as day_name_short,
        case
            when date_part('dow', date_actual) in (0, 6) then 1
            else 0
        end as is_weekend,

        -- Fiscal (assuming fiscal year = calendar year for simplicity)
        date_part('year', date_actual) as fiscal_year,
        date_part('quarter', date_actual) as fiscal_quarter,

        -- Date parts for joins
        date_trunc('month', date_actual) as month_start_date,
        date_trunc('year', date_actual) as year_start_date,

        -- First/last day of month
        date_actual - (date_part('day', date_actual) - 1) as first_day_of_month,
        (date_trunc('month', date_actual) + interval '1 month' - interval '1 day')::date as last_day_of_month,

        -- Season
        case
            when date_part('month', date_actual) in (12, 1, 2) then 'Winter'
            when date_part('month', date_actual) in (3, 4, 5) then 'Spring'
            when date_part('month', date_actual) in (6, 7, 8) then 'Summer'
            when date_part('month', date_actual) in (9, 10, 11) then 'Fall'
        end as season,

        -- Holiday flags (US holidays for portfolio context)
        case
            when date_part('month', date_actual) = 1 and date_part('day', date_actual) = 1 then 'New Year'
            when date_part('month', date_actual) = 2 and date_part('day', date_actual) = 14 then 'Valentine'
            when date_part('month', date_actual) = 12 and date_part('day', date_actual) = 25 then 'Christmas'
            when date_part('month', date_actual) = 12 and date_part('day', date_actual) = 31 then 'New Year Eve'
            else null
        end as holiday_name,

        case
            when date_part('month', date_actual) = 1 and date_part('day', date_actual) = 1 then 1
            when date_part('month', date_actual) = 2 and date_part('day', date_actual) = 14 then 1
            when date_part('month', date_actual) = 12 and date_part('day', date_actual) = 25 then 1
            when date_part('month', date_actual) = 12 and date_part('day', date_actual) = 31 then 1
            else 0
        end as is_holiday

    from date_spine
)

select * from date_dim
