-- Q6: departments where paid overtime exceeds computed overtime by more than 15% (all six months together)
WITH emd AS (
    SELECT m.month, e.emp_id, e.department_key
    FROM warehouse.dim_month m
    JOIN warehouse.dim_employee e
      ON e.hire_date <= m.month_end
     AND (e.separation_date IS NULL OR e.separation_date >= m.month_start)
     AND MIN(m.month_end, COALESCE(e.separation_date, m.month_end)) BETWEEN e.valid_from AND e.valid_to
),
cur AS (SELECT emp_id, department_key FROM warehouse.dim_employee WHERE is_current = 1),
comp AS (
    SELECT d.month_key AS month, f.emp_id, SUM(f.overtime_hours) AS hrs
    FROM warehouse.fact_attendance_daily f JOIN warehouse.dim_date d ON d.date_key = f.date_key
    GROUP BY d.month_key, f.emp_id
),
paid AS (
    SELECT f.payroll_month AS month, f.emp_id, SUM(f.units) AS hrs
    FROM warehouse.fact_payroll_line f WHERE f.component = 'OVERTIME'
    GROUP BY f.payroll_month, f.emp_id
),
keys AS (SELECT month, emp_id FROM comp UNION SELECT month, emp_id FROM paid),
dept AS (
    SELECT dp.plant_name, dp.dept_name,
           SUM(COALESCE(comp.hrs, 0)) AS computed_hours,
           SUM(COALESCE(paid.hrs, 0)) AS paid_hours
    FROM keys k
    LEFT JOIN comp ON comp.month = k.month AND comp.emp_id = k.emp_id
    LEFT JOIN paid ON paid.month = k.month AND paid.emp_id = k.emp_id
    LEFT JOIN emd  ON emd.month  = k.month AND emd.emp_id  = k.emp_id
    LEFT JOIN cur  ON cur.emp_id = k.emp_id
    JOIN warehouse.dim_department dp ON dp.department_key = COALESCE(emd.department_key, cur.department_key, 0)
    GROUP BY dp.plant_name, dp.dept_name
)
SELECT plant_name AS plant, dept_name AS department,
       ROUND(computed_hours, 1) AS computed_ot_hours,
       ROUND(paid_hours, 1) AS paid_ot_hours,
       ROUND(paid_hours - computed_hours, 1) AS excess_hours,
       ROUND(100.0 * (paid_hours - computed_hours) / NULLIF(computed_hours, 0), 1) AS excess_pct
FROM dept
WHERE paid_hours > computed_hours * 1.15
ORDER BY excess_hours DESC;
