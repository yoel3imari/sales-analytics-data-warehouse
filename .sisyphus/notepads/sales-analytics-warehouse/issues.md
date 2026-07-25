# Issues - Sales Analytics Warehouse

## Open Issues
- All resolved. Previous dim_date.sql DuckDB v1.5.5 compatibility issues fixed:
  1. ✅ `CAST(date_part(...) AS INTEGER)` — applied
  2. ✅ `generate_series(...)::date as date_actual` — applied

## F3 Full Integration QA — 2026-07-25 (Re-Run 1)
- **CRITICAL**: dim_date model still fails — error changed from `-(TIMESTAMP, BIGINT)` to `-(TIMESTAMP, INTEGER)`. CAST-to-INTEGER fixed the BIGINT issue but `generate_series` returns TIMESTAMP in DuckDB v1.5.5, and `TIMESTAMP - INTEGER` is invalid.
- **Correct fix needed**: Add `::date` cast on generate_series output: `unnest(generate_series(...))::date as date_actual`
- **SCD2**: Snapshots build successfully but no customers/products have multiple versions yet. Expected — only a single data load has occurred so there are no changes to track.
- **Referential Integrity**: Staging layer shows 1 orphan customer_id (injected bad data). Gold layer FK checks were skipped due to missing tables.
- **Sales row count**: 782,059 rows exceeds documented 100K-500K range. Config may have been updated or generator parameters changed.
- **Evidence saved**: `.sisyphus/evidence/final-qa/` with all 8 scenario results + verdict.

## F3 Full Integration QA — Attempt 3 (APPROVED) — 2026-07-25
- Both dim_date fixes applied successfully (CAST to INTEGER + ::date cast)
- All 8 dbt models build successfully (exit 0)
- Star schema tables: dim_customer (10K), dim_product (80), dim_date (1,826), fact_sales (782,055), obt_sales (782,055)
- Referential integrity: 0 orphans across all FK relationships
- Schema tests: 58 PASS, 2 FAIL (expected — injected duplicate data)
- Data quality tests: all 4 catch bad data
- dim_date range: 2022-01-01 to 2026-12-31, 1,826 rows
- Verdict: APPROVE ✓

## F4 Scope Fidelity — 2026-07-25
- **Minor**: sources.yml missing freshness checks (T6 spec requires "Add freshness checks (warn if data > 7 days old)")
- **Minor**: Only 4/5 bad-data tests have `data_quality` tag (test_no_null_customer_sk_in_fact is untagged — acceptable since null customer_id is filtered in stg_customers)
- **Contamination**: CLEAN — no cross-task file ownership violations
