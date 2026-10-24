-- Q9: payroll cost per employee by department with month-over-month change
-- payroll cost = sum of EARNING lines (rule 21); department on the last day of the month (rule 3)
WITH emd AS (
    SELECT m.month, e.emp_id, e.department_key
    FROM warehouse.dim_month m
    JOIN warehouse.dim_employee e
      ON e.hire_date <= m.month_end
     AND (e.separation_date IS NULL OR e.separation_date >= m.month_start)
     AND MIN(m.month_end, COALESCE(e.separation_date, m.month_end)) BETWEEN e.valid_from AND e.valid_to
),
cur AS (SELECT emp_id, department_key FROM warehouse.dim_employee WHERE is_current = 1),
pay AS (
    SELECT f.payroll_month AS month, f.emp_id, SUM(f.amount) AS cost
    FROM warehouse.fact_payroll_line f
    WHERE f.component_type = 'EARNING'
    GROUP BY f.payroll_month, f.emp_id
),
dept_month AS (
    SELECT p.month, COALESCE(emd.department_key, cur.department_key, 0) AS department_key,
           SUM(p.cost) AS total_cost, COUNT(DISTINCT p.emp_id) AS paid_employees
    FROM pay p
    LEFT JOIN emd ON emd.month = p.month AND emd.emp_id = p.emp_id
    LEFT JOIN cur ON cur.emp_id = p.emp_id
    GROUP BY p.month, COALESCE(emd.department_key, cur.department_key, 0)
),
calc AS (
    SELECT department_key, month, total_cost, paid_employees,
           total_cost / paid_employees AS cost_per_employee
    FROM dept_month
),
win AS (
    SELECT c.*, LAG(c.cost_per_employee) OVER (PARTITION BY c.department_key ORDER BY c.month) AS prev_cost
    FROM calc c
)
SELECT dp.plant_name AS plant, dp.dept_name AS department, w.month,
       ROUND(w.total_cost, 2) AS total_payroll_cost,
       w.paid_employees,
       ROUND(w.cost_per_employee, 2) AS cost_per_employee,
       ROUND(w.cost_per_employee - w.prev_cost, 2) AS mom_change,
       ROUND(100.0 * (w.cost_per_employee - w.prev_cost) / NULLIF(w.prev_cost, 0), 2) AS mom_change_pct
FROM win w
JOIN warehouse.dim_department dp ON dp.department_key = w.department_key
ORDER BY dp.plant_name, dp.dept_name, w.month;
