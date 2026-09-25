-- ============================================================
-- Sales Data ETL Pipeline - Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS sales_analytics;
USE sales_analytics;

DROP TABLE IF EXISTS sales_fact;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;

-- Customers dimension table
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(150) UNIQUE
);

-- Products dimension table
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    UNIQUE KEY uq_product_category (product_name, category)
);

-- Cleaned, transformed sales fact table (this is what the ETL loads into)
CREATE TABLE sales_fact (
    order_id INT PRIMARY KEY,
    customer_id INT,
    product_id INT,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    order_date DATE NOT NULL,
    region VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX idx_order_date ON sales_fact(order_date);
CREATE INDEX idx_region ON sales_fact(region);
