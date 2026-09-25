-- ============================================================
-- Sales Analytics - Reporting Queries
-- ============================================================
USE sales_analytics;

-- 1. Total revenue and orders by product category
SELECT
    p.category,
    COUNT(s.order_id)      AS total_orders,
    SUM(s.quantity)        AS total_units_sold,
    SUM(s.total_amount)    AS total_revenue
FROM sales_fact s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;

-- 2. Revenue by region
SELECT
    region,
    COUNT(order_id)     AS total_orders,
    SUM(total_amount)   AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM sales_fact
GROUP BY region
ORDER BY total_revenue DESC;

-- 3. Top 5 customers by total spend
SELECT
    c.customer_name,
    c.customer_email,
    COUNT(s.order_id)   AS total_orders,
    SUM(s.total_amount) AS total_spend
FROM sales_fact s
JOIN customers c ON s.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.customer_email
ORDER BY total_spend DESC
LIMIT 5;

-- 4. Monthly sales trend
SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS month,
    SUM(total_amount) AS monthly_revenue,
    COUNT(order_id)   AS monthly_orders
FROM sales_fact
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY month;

-- 5. Best-selling products (by units and revenue)
SELECT
    p.product_name,
    p.category,
    SUM(s.quantity)     AS units_sold,
    SUM(s.total_amount) AS revenue
FROM sales_fact s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY units_sold DESC;

-- 6. Orders filtered above a revenue threshold (e.g., high-value orders)
SELECT
    s.order_id,
    c.customer_name,
    p.product_name,
    s.total_amount,
    s.order_date
FROM sales_fact s
JOIN customers c ON s.customer_id = c.customer_id
JOIN products p ON s.product_id = p.product_id
WHERE s.total_amount > 50
ORDER BY s.total_amount DESC;

-- 7. Customers who ordered from more than one category (cross-category buyers)
SELECT
    c.customer_name,
    COUNT(DISTINCT p.category) AS distinct_categories
FROM sales_fact s
JOIN customers c ON s.customer_id = c.customer_id
JOIN products p ON s.product_id = p.product_id
GROUP BY c.customer_id, c.customer_name
HAVING COUNT(DISTINCT p.category) > 1
ORDER BY distinct_categories DESC;
