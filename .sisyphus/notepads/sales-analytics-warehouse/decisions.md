# Decisions - Sales Analytics Warehouse

## Architecture Decisions
1. **DuckDB as warehouse**: Embedded, zero-infra, perfect for portfolio
2. **dbt in separate container**: Clean separation from Airflow, triggered via DockerOperator
3. **Generator → CSV → COPY INTO**: Classic ELT pattern
4. **Single DuckDB file**: `/data/warehouse/sales_analytics.duckdb`, shared via Docker volume
5. **Manual DAG trigger**: Generator produces all 3 years at once
6. **dbt profiles.yml checked into repo**: No credentials needed for DuckDB
7. **Single fact table (fact_sales)**: No scope creep
8. **SCD Type 2 on customer + product only**: check strategy
9. **Linear DAG only**: No branching, sensors, subDAGs
10. **Debian-based Metabase**: DuckDB JDBC has glibc issues on Alpine
11. **No dbt macros/over-abstraction**: Inline SQL is fine
12. **Bad data injection**: 5 intentionally bad records to demonstrate dbt quality tests
