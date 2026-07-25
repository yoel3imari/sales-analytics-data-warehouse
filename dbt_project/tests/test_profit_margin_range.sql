-- Singular test: Profit margin should be within reasonable range (-100% to 100%)
-- Margins outside this range indicate data quality issues
{{ config(severity='warn') }}

select
    order_line_sk,
    order_id,
    profit_margin_pct
from {{ ref('fact_sales') }}
where profit_margin_pct < -100 or profit_margin_pct > 100
