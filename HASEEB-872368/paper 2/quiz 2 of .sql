---quiz 2----------
--------task>1-------
--Task 1 — Build the Sales Detail Dataset (6 marks)
--Management needs a detailed sales dataset for analysis. Return one row per order item containing:
--order_id and order_date
--customer full name
--store name
--staff full name
--product name
--category name
--brand name
--quantity, list_price, discount
--calculated net_line_revenue

--Include only completed orders (order_status = 4). Sort the result from newest order to oldest.

SELECT
    o.order_id,
    o.order_date,
    c.first_name + ' ' + c.last_name AS customer_full_name,
    s.store_name,
    st.first_name + ' ' + st.last_name AS staff_full_name,
    p.product_name,
    cat.category_name,
    b.brand_name,
    oi.quantity,
    oi.list_price,
    oi.discount,
    oi.quantity * oi.list_price * (1 - oi.discount)
        AS net_line_revenue

FROM sales.orders AS o

INNER JOIN sales.customers AS c
    ON o.customer_id = c.customer_id

INNER JOIN sales.stores AS s
    ON o.store_id = s.store_id

INNER JOIN sales.staffs AS st
    ON o.staff_id = st.staff_id

INNER JOIN sales.order_items AS oi
    ON o.order_id = oi.order_id

INNER JOIN production.products AS p
    ON oi.product_id = p.product_id

INNER JOIN production.categories AS cat
    ON p.category_id = cat.category_id

INNER JOIN production.brands AS b
    ON p.brand_id = b.brand_id

WHERE o.order_status = 4

ORDER BY o.order_date DESC;

----/* Task 2 — Store Performance Summary (5 marks)
--Create a store-level performance report for completed orders showing:
--store name
--number of distinct orders
--total units sold
--total net revenue
--average order value

--Return one row per store and order the stores from highest to lowest total net revenue.

SELECT
    s.store_name,

    COUNT(DISTINCT o.order_id) AS number_of_distinct_orders,
    SUM(oi.quantity) AS total_units_sold,
    SUM(
        oi.quantity * oi.list_price * (1 - oi.discount)
    ) AS total_net_revenue,
    CAST(
        SUM(
            oi.quantity * oi.list_price * (1 - oi.discount)
        )
        / NULLIF(COUNT(DISTINCT o.order_id), 0)
        AS DECIMAL(12, 2)
    ) AS average_order_value

FROM sales.stores AS s
LEFT JOIN sales.orders AS o
    ON s.store_id = o.store_id
    AND o.order_status = 4

LEFT JOIN sales.order_items AS oi
    ON o.order_id = oi.order_id
GROUP BY
    s.store_id,
    s.store_name

ORDER BY
    total_net_revenue DESC;


--/*Task 3 — High-Value Customers (5 marks)
--Management wants to identify high-value customers. Return customers whose total completed-order spending is greater than the average total spending of customers who have completed orders.

WITH customer_spending AS
(
    SELECT
        c.customer_id,
        c.first_name + ' ' + c.last_name AS customer_name,

        COUNT(DISTINCT o.order_id) AS completed_order_count,

        SUM(
            oi.quantity * oi.list_price * (1 - oi.discount)
        ) AS total_spending

    FROM sales.customers AS c

    INNER JOIN sales.orders AS o
        ON c.customer_id = o.customer_id

    INNER JOIN sales.order_items AS oi
        ON o.order_id = oi.order_id

    WHERE o.order_status = 4

    GROUP BY
        c.customer_id,
        c.first_name,
        c.last_name
)

SELECT
    customer_id,
    customer_name,
    completed_order_count,
    total_spending

FROM customer_spending

WHERE total_spending >
(
    SELECT AVG(total_spending)
    FROM customer_spending
)

ORDER BY
    total_spending DESC;

--/* Task 4 — Inventory Risk Report (5 marks)
--Operations wants to identify inventory risk. Return products where the stock quantity is below 5 in at least one store.
--Show product name, store name, current quantity, category name, and brand name. Products with zero stock should appear first, followed by the lowest remaining quantities.

SELECT
    p.product_name,
    s.store_name,
    st.quantity AS current_quantity,
    c.category_name,
    b.brand_name

FROM production.stocks AS st

INNER JOIN production.products AS p
    ON st.product_id = p.product_id

INNER JOIN sales.stores AS s
    ON st.store_id = s.store_id

INNER JOIN production.categories AS c
    ON p.category_id = c.category_id

INNER JOIN production.brands AS b
    ON p.brand_id = b.brand_id

WHERE st.quantity < 5

ORDER BY
    st.quantity ASC,
    p.product_name;

--/*Task 5 — Top Products Within Each Category (6 marks)
--For each product category, identify the top 3 products by total net revenue from completed orders.

--Return category name, product name, total units sold, total net revenue, and the product's position within its category. Tied products must receive the same position and the next position should not contain gaps.

WITH product_sales AS
(
    SELECT
        c.category_id,
        c.category_name,
        p.product_id,
        p.product_name,

        SUM(oi.quantity) AS total_units_sold,

        SUM(
            oi.quantity * oi.list_price * (1 - oi.discount)
        ) AS total_net_revenue

    FROM production.categories AS c

    INNER JOIN production.products AS p
        ON c.category_id = p.category_id

    INNER JOIN sales.order_items AS oi
        ON p.product_id = oi.product_id

    INNER JOIN sales.orders AS o
        ON oi.order_id = o.order_id

    WHERE o.order_status = 4

    GROUP BY
        c.category_id,
        c.category_name,
        p.product_id,
        p.product_name
),

ranked_products AS
(
    SELECT
        category_name,
        product_name,
        total_units_sold,
        total_net_revenue,

        DENSE_RANK() OVER
        (
            PARTITION BY category_id
            ORDER BY total_net_revenue DESC
        ) AS product_position

    FROM product_sales
)

SELECT
    category_name,
    product_name,
    total_units_sold,
    total_net_revenue,
    product_position

FROM ranked_products

WHERE product_position <= 3

ORDER BY
    category_name,
    product_position,
    product_name;



--/*Task 6 — Monthly Sales Trend (6 marks)
--Create a monthly sales trend for completed orders.
--For each calendar month return:
--year
--month
--total net revenue
--previous month's total net revenue
--revenue change from the previous month
--The first month may have NULL for the previous-month comparison. Sort chronologically.

WITH monthly_sales AS
(
    SELECT
        YEAR(o.order_date) AS sales_year,
        MONTH(o.order_date) AS sales_month,

        SUM(
            oi.quantity * oi.list_price * (1 - oi.discount)
        ) AS total_net_revenue

    FROM sales.orders AS o

    INNER JOIN sales.order_items AS oi
        ON o.order_id = oi.order_id

    WHERE o.order_status = 4

    GROUP BY
        YEAR(o.order_date),
        MONTH(o.order_date)
),

monthly_with_previous AS
(
    SELECT
        sales_year,
        sales_month,
        total_net_revenue,

        LAG(total_net_revenue) OVER
        (
            ORDER BY sales_year, sales_month
        ) AS previous_month_total_net_revenue

    FROM monthly_sales
)

SELECT
    sales_year,
    sales_month,
    total_net_revenue,
    previous_month_total_net_revenue,

    total_net_revenue
        - previous_month_total_net_revenue
        AS revenue_change_from_previous_month

FROM monthly_with_previous

ORDER BY
    sales_year,
    sales_month;



--/*Task 7 — Reusable Reporting View (4 marks)
--Create a view named sales.vw_customer_sales_summary that returns one row per customer and includes:
--customer_id
--customer full name
--total number of completed orders
--total units purchased
--total net revenue
--most recent completed order date

--Customers with no completed orders must still be represented where possible, with appropriate zero/NULL values.

CREATE OR ALTER VIEW sales.vw_customer_sales_summary
AS

SELECT
    c.customer_id,

    c.first_name + ' ' + c.last_name AS customer_full_name,

    COUNT(DISTINCT o.order_id) AS total_completed_orders,

    COALESCE(
        SUM(oi.quantity),
        0
    ) AS total_units_purchased,

    COALESCE(
        SUM(
            oi.quantity * oi.list_price * (1 - oi.discount)
        ),
        0
    ) AS total_net_revenue,

    MAX(o.order_date) AS most_recent_completed_order_date

FROM sales.customers AS c

LEFT JOIN sales.orders AS o
    ON c.customer_id = o.customer_id
    AND o.order_status = 4

LEFT JOIN sales.order_items AS oi
    ON o.order_id = oi.order_id

GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name;



--/* Test the view */--

SELECT *
FROM sales.vw_customer_sales_summary

ORDER BY total_net_revenue DESC;



--/* Task 8 — Safe Data Modification (4 marks)
--A customer with customer_id = 1 has requested that their phone number be changed to '(999) 555-0101'.
--Write SQL that performs this update inside an explicit transaction. Include a validation query after the UPDATE and show how the change can be rolled back during testing so the assessment database is not permanently changed.

BEGIN TRANSACTION;

UPDATE sales.customers
SET phone = '(999) 555-0101'
WHERE customer_id = 1;


--/* Validation query */--

SELECT
    customer_id,
    first_name,
    last_name,
    phone
FROM sales.customers
WHERE customer_id = 1;


--/*
  --  Testing:
  -- The change can be rolled back so the original
  -- database remains unchanged.
--*/

ROLLBACK TRANSACTION;



--/*Task 9 — Store Sales Procedure (6 marks)
--Create a stored procedure named sales.usp_store_sales_report with these input parameters:
--@store_id
--@start_date
--@end_date

CREATE OR ALTER PROCEDURE sales.usp_store_sales_report
    @store_id INT,
    @start_date DATE,
    @end_date DATE
AS
BEGIN

    SET NOCOUNT ON;

    BEGIN TRY

        /* Validate date range */

        IF @start_date > @end_date
        BEGIN
            THROW 50001,
                  'Start date cannot be later than end date.',
                  1;
        END;


        /* Store sales report */

        SELECT
            p.product_name,

            SUM(oi.quantity) AS total_units_sold,

            SUM(
                oi.quantity
                * oi.list_price
                * (1 - oi.discount)
            ) AS total_net_revenue

        FROM sales.orders AS o

        INNER JOIN sales.order_items AS oi
            ON o.order_id = oi.order_id

        INNER JOIN production.products AS p
            ON oi.product_id = p.product_id

        WHERE
            o.store_id = @store_id
            AND o.order_status = 4
            AND o.order_date >= @start_date
            AND o.order_date < DATEADD(DAY, 1, @end_date)

        GROUP BY
            p.product_id,
            p.product_name

        ORDER BY
            total_net_revenue DESC;

    END TRY

    BEGIN CATCH

        THROW;

    END CATCH;

END;



/* Example procedure execution */

EXEC sales.usp_store_sales_report
    @store_id = 1,
    @start_date = '2016-01-01',
    @end_date = '2018-12-31';


-----/* Task 10 — Management Insight Query (3 marks)
--Write one additional SQL query that you believe would provide useful insight to BikeStores management using at least three tables.

--Below the query, add a SQL comment of no more than three lines explaining:
--1. the business question,
--2. what the result measures, and
--3. why management should care about it.



SELECT
    s.store_name,
    p.product_name,

    SUM(oi.quantity) AS total_units_sold,

    SUM(
        oi.quantity * oi.list_price * (1 - oi.discount)
    ) AS total_net_revenue

FROM sales.stores AS s

INNER JOIN sales.orders AS o
    ON s.store_id = o.store_id

INNER JOIN sales.order_items AS oi
    ON o.order_id = oi.order_id

INNER JOIN production.products AS p
    ON oi.product_id = p.product_id

WHERE o.order_status = 4

GROUP BY
    s.store_id,
    s.store_name,
    p.product_id,
    p.product_name

ORDER BY
    s.store_name,
    total_net_revenue DESC;

/*
============================================================
END OF ASSIGNMENT
TOTAL MARKS: 50
============================================================
*/
