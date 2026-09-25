# 📊 Sales Data ETL & Analytics Pipeline

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A end-to-end ETL pipeline that extracts raw, messy sales data, cleans and
transforms it with **Pandas**, loads it into a normalized **MySQL** schema,
and generates sales & customer analytics with **SQL**.

## ✨ Features

- 🔍 **Extract** — reads raw sales records from CSV
- 🧹 **Clean** — handles missing values, removes duplicate orders, fixes inconsistent formats (mixed date formats, inconsistent text casing)
- ✅ **Validate** — coerces numeric fields, drops invalid records (negative prices/quantities)
- 🔄 **Transform** — derives `total_amount`, `order_month` for reporting
- 🗄️ **Load** — writes into a normalized MySQL star schema (`customers`, `products`, `sales_fact`) with idempotent upserts
- 📈 **Analyze** — sales-by-category, sales-by-region, top customers, monthly trends — via both Pandas and SQL

## 🗂️ Project Structure

```
sales_etl_project/
├── data/
│   └── raw_sales_data.csv       # sample raw/messy input data
├── sql/
│   ├── schema.sql               # MySQL table definitions
│   └── analysis_queries.sql     # reporting queries (joins, aggregation, filters)
├── output/
│   └── cleaned_sales_data.csv   # ETL output (generated on run)
├── etl_pipeline.py              # main ETL script
├── requirements.txt
├── LICENSE
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- MySQL 8.0+

### Installation
```bash
git clone https://github.com/<your-username>/sales-etl-pipeline.git
cd sales-etl-pipeline
pip install -r requirements.txt
```

### Set up the database
```bash
mysql -u root -p < sql/schema.sql
```

Update the `DB_CONFIG` dictionary in `etl_pipeline.py` with your MySQL
credentials (or set them as environment variables for production use).

### Run the pipeline
```bash
python etl_pipeline.py
```

This will:
1. Extract raw data from `data/raw_sales_data.csv`
2. Clean & transform it with Pandas
3. Save the cleaned dataset to `output/cleaned_sales_data.csv`
4. Print sales/customer summaries to the console
5. Load the cleaned data into MySQL (skipped gracefully if no DB connection is available)

### Run the analytics queries
```bash
mysql -u root -p sales_analytics < sql/analysis_queries.sql
```

## 🧪 Data Quality Issues Handled

| Issue | Example | How it's handled |
|---|---|---|
| Missing values | blank email, missing quantity | filled with sensible defaults or dropped if unrecoverable |
| Duplicate records | same order entered twice | de-duplicated on customer + product + date + quantity |
| Inconsistent formats | `2024-01-05`, `01/06/2024`, `2024/01/09` | parsed into a single standardized `datetime` |
| Inconsistent casing | `Electronics` vs `electronics` | normalized with `.str.title()` |
| Invalid values | negative price | validated and dropped |

## 📊 Sample Output

```
=== Sales by Category ===
Furniture      896.95
Electronics    349.79
Stationery     129.74

=== Sales by Region ===
East     534.38
South    374.33
North    354.80
West     112.97
```

## 🛠️ Tech Stack
Python · Pandas · NumPy · MySQL · SQL

## 🔮 Future Improvements
- Batch inserts (`executemany`) instead of row-by-row loading
- Orchestration with Airflow or a scheduled cron job
- `.env`-based configuration instead of hardcoded credentials
- Incremental/delta loads instead of full reprocessing
- Unit tests for each transformation step

## 📄 License
This project is licensed under the [MIT License](LICENSE).
