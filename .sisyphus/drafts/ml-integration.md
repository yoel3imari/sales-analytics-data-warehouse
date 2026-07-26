# Draft: ML Integration in Sales Analytics

## Current Project Snapshot
- **Raw data**: 10K customers, 80 products, ~782K sales line items (78MB CSV)
- **Star schema**: dim_customer (SCD2), dim_product (SCD2), dim_date, fact_sales, obt_sales (denormalized)
- **Customers**: demographics + cohort (LOYAL_HEAVY/LOYAL_LIGHT/GROWING/DECLINING/ONE_SHOT/CHURN_RISK) + income_bracket, age, gender
- **Customer metrics**: total_orders, total_revenue, total_profit, avg_order_value, days_since_last_order, value/frequency/recency segments, customer_tier
- **Product metrics**: total_units_sold, total_revenue, profit_rank, volume_rank
- **Temporal patterns**: annual seasonality (monthly multipliers 0.7-1.8), day-of-week multipliers, holiday spikes (BF/CM/Xmas/Valentine's)
- **Pipeline**: Python Faker generator → DuckDB → dbt (staging/int/marts) → Metabase dashboards
- **Orchestration**: Airflow DAG (8 tasks)
- **Infrastructure**: DuckDB (embedded), Python 3.12, Docker for Airflow+Metabase

## Data Available for ML

### Customer-Level Features (10K rows)
- Demographics: age, gender, income_bracket
- Behavioral: cohort, total_orders, total_revenue, total_profit, avg_order_value, days_since_last_order
- Derived: value_segment, frequency_segment, recency_segment, customer_tier
- Temporal: signup_date, first_order_date, last_order_date

### Product-Level Features (80 rows)
- Attributes: category, subcategory, brand, list_price, standard_cost, markup_pct
- Performance: total_units_sold, total_revenue, total_profit, avg_profit_margin_pct, ranks
- Status: ACTIVE/DISCONTINUED

### Transaction-Level Features (782K rows)
- Order: order_id, order_date, quantity, unit_price, discount_amount, channel, ship_window
- Temporal: day_of_week, month, season, is_holiday, holiday_name

## Potential ML Use Cases (identified)
1. **CLV Prediction** - predict future revenue/profit per customer
2. **Churn Prediction** - predict which customers will churn next period
3. **Next Purchase Prediction** - predict when customer will order again
4. **Product Recommendation** - personalized product suggestions
5. **Demand Forecasting** - predict sales volume by category/time
6. **Price Elasticity** - predict optimal discount/price
7. **Customer Segmentation** - discover natural clusters beyond synthetic cohorts
8. **Anomaly Detection** - flag unusual purchase patterns

## Technical Options (to discuss)
- **A: DuckDB ML + Python** - train/score in-warehouse, light infra
- **B: Airflow ML pipeline** - extend existing DAG with ML task
- **C: FastAPI + MLflow** - separate serving layer, more production-oriented
