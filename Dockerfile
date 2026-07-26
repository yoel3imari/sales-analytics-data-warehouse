FROM python:3.12-slim

WORKDIR /dbt_project

# Install dbt-core and DuckDB adapter matching project specifications
RUN pip install --no-cache-dir \
    dbt-core>=1.12.0 \
    dbt-duckdb>=1.10.1

# Copy dbt project files
COPY dbt_project/ /dbt_project/

# Default entrypoint: dbt
ENTRYPOINT ["dbt"]
CMD ["--help"]
