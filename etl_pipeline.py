"""
Sales Data ETL and Analytics Pipeline
======================================
Extracts raw sales data (CSV), cleans and transforms it with Pandas,
and loads it into a MySQL database for analysis.

Author: <your name>
Tech: Python, Pandas, MySQL (mysql-connector-python), SQL
"""

import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
import logging

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",   # change this
    "database": "sales_analytics",
}

RAW_DATA_PATH = "data/raw_sales_data.csv"
CLEAN_DATA_PATH = "output/cleaned_sales_data.csv"


# ------------------------------------------------------------------
# EXTRACT
# ------------------------------------------------------------------
def extract(path: str) -> pd.DataFrame:
    """Read raw sales data from CSV into a DataFrame."""
    logger.info(f"Extracting data from {path}")
    df = pd.read_csv(path)
    logger.info(f"Extracted {len(df)} raw records")
    return df


# ------------------------------------------------------------------
# TRANSFORM
# ------------------------------------------------------------------
def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values for key columns."""
    before = len(df)

    # Drop rows with no customer name at all (can't identify the customer)
    df = df[df["customer_name"].notna() & (df["customer_name"].str.strip() != "")]

    # Fill missing quantity with 1 (assume minimum order quantity)
    df["quantity"] = df["quantity"].fillna(1)

    # Fill missing email with a placeholder based on name
    df["customer_email"] = df.apply(
        lambda row: row["customer_email"]
        if pd.notna(row["customer_email"]) and str(row["customer_email"]).strip() != ""
        else f"{row['customer_name'].lower().replace(' ', '.')}@unknown.com",
        axis=1,
    )

    logger.info(f"Missing value handling: {before} -> {len(df)} records")
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate orders (same customer, product, date, qty)."""
    before = len(df)
    df = df.drop_duplicates(
        subset=["customer_name", "product", "order_date", "quantity"],
        keep="first",
    )
    logger.info(f"Duplicate removal: {before} -> {len(df)} records")
    return df


def standardize_formats(df: pd.DataFrame) -> pd.DataFrame:
    """Fix inconsistent formats: dates, category casing, text whitespace."""
    df["customer_name"] = df["customer_name"].str.strip()
    df["product"] = df["product"].str.strip()
    df["category"] = df["category"].str.strip().str.title()  # electronics -> Electronics
    df["region"] = df["region"].str.strip().str.title()

    # Parse dates that come in multiple formats (YYYY-MM-DD, MM/DD/YYYY, YYYY/MM/DD)
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce", format="mixed")

    # Drop rows where date parsing failed
    df = df[df["order_date"].notna()]

    return df


def validate_and_correct(df: pd.DataFrame) -> pd.DataFrame:
    """Validate numeric fields and fix/remove invalid records."""
    before = len(df)

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    # Remove rows with negative or zero prices/quantities (bad data)
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)]

    # Drop any remaining nulls in critical fields
    df = df.dropna(subset=["quantity", "unit_price", "order_date"])

    logger.info(f"Validation: {before} -> {len(df)} records")
    return df


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived fields needed for analysis."""
    df["total_amount"] = (df["quantity"] * df["unit_price"]).round(2)
    df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full transformation pipeline."""
    logger.info("Starting transformation stage")
    df = clean_missing_values(df)
    df = standardize_formats(df)
    df = remove_duplicates(df)
    df = validate_and_correct(df)
    df = enrich(df)
    logger.info(f"Transformation complete. Final record count: {len(df)}")
    return df


# ------------------------------------------------------------------
# LOAD
# ------------------------------------------------------------------
def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            logger.info("Connected to MySQL database")
        return conn
    except Error as e:
        logger.error(f"MySQL connection failed: {e}")
        raise


def load(df: pd.DataFrame):
    """Load cleaned data into MySQL: customers, products, sales_fact."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        for _, row in df.iterrows():
            # Upsert customer
            cursor.execute(
                """INSERT INTO customers (customer_name, customer_email)
                   VALUES (%s, %s)
                   ON DUPLICATE KEY UPDATE customer_name = VALUES(customer_name)""",
                (row["customer_name"], row["customer_email"]),
            )
            cursor.execute(
                "SELECT customer_id FROM customers WHERE customer_email = %s",
                (row["customer_email"],),
            )
            customer_id = cursor.fetchone()[0]

            # Upsert product
            cursor.execute(
                """INSERT INTO products (product_name, category)
                   VALUES (%s, %s)
                   ON DUPLICATE KEY UPDATE product_name = VALUES(product_name)""",
                (row["product"], row["category"]),
            )
            cursor.execute(
                "SELECT product_id FROM products WHERE product_name = %s AND category = %s",
                (row["product"], row["category"]),
            )
            product_id = cursor.fetchone()[0]

            # Insert sales fact (ignore if order_id already loaded)
            cursor.execute(
                """INSERT IGNORE INTO sales_fact
                   (order_id, customer_id, product_id, quantity, unit_price,
                    total_amount, order_date, region)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    int(row["order_id"]),
                    customer_id,
                    product_id,
                    int(row["quantity"]),
                    float(row["unit_price"]),
                    float(row["total_amount"]),
                    row["order_date"].date(),
                    row["region"],
                ),
            )

        conn.commit()
        logger.info(f"Loaded {len(df)} records into MySQL")

    except Error as e:
        conn.rollback()
        logger.error(f"Load failed, rolled back transaction: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------------
# ANALYSIS (basic Pandas-side summaries, in addition to SQL reporting)
# ------------------------------------------------------------------
def generate_summaries(df: pd.DataFrame):
    logger.info("Generating sales and customer summaries")

    sales_by_category = (
        df.groupby("category")["total_amount"].sum().sort_values(ascending=False)
    )
    sales_by_region = (
        df.groupby("region")["total_amount"].sum().sort_values(ascending=False)
    )
    top_customers = (
        df.groupby("customer_name")["total_amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )
    monthly_trend = df.groupby("order_month")["total_amount"].sum()

    print("\n=== Sales by Category ===")
    print(sales_by_category)

    print("\n=== Sales by Region ===")
    print(sales_by_region)

    print("\n=== Top 5 Customers ===")
    print(top_customers)

    print("\n=== Monthly Sales Trend ===")
    print(monthly_trend)


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
def main():
    raw_df = extract(RAW_DATA_PATH)
    clean_df = transform(raw_df)

    clean_df.to_csv(CLEAN_DATA_PATH, index=False)
    logger.info(f"Cleaned data saved to {CLEAN_DATA_PATH}")

    generate_summaries(clean_df)

    # Comment out load() if you don't have MySQL set up locally
    try:
        load(clean_df)
    except Exception as e:
        logger.warning(f"Skipping MySQL load (DB not available?): {e}")


if __name__ == "__main__":
    main()
