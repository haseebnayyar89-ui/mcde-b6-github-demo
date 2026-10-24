-- Q5: overtime hours computed from punches vs approved vs paid, by department and month
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
appr AS (
    SELECT d.month_key AS month, f.emp_id, SUM(f.approved_hours) AS hrs
    FROM warehouse.fact_overtime_approved f JOIN warehouse.dim_date d ON d.date_key = f.date_key
    GROUP BY d.month_key, f.emp_id
),
paid AS (
    SELECT f.payroll_month AS month, f.emp_id, SUM(f.units) AS hrs
    FROM warehouse.fact_payroll_line f WHERE f.component = 'OVERTIME'
    GROUP BY f.payroll_month, f.emp_id
),
keys AS (
    SELECT month, emp_id FROM comp UNION SELECT month, emp_id FROM appr UNION SELECT month, emp_id FROM paid
)
SELECT k.month, dp.plant_name AS plant, dp.dept_name AS department,
       ROUND(SUM(COALESCE(comp.hrs, 0)), 1) AS computed_ot_hours,
       ROUND(SUM(COALESCE(appr.hrs, 0)), 1) AS approved_ot_hours,
       ROUND(SUM(COALESCE(paid.hrs, 0)), 1) AS paid_ot_hours,
       ROUND(SUM(COALESCE(paid.hrs, 0)) - SUM(COALESCE(comp.hrs, 0)), 1) AS paid_minus_computed
FROM keys k
LEFT JOIN comp ON comp.month = k.month AND comp.emp_id = k.emp_id
LEFT JOIN appr ON appr.month = k.month AND appr.emp_id = k.emp_id
LEFT JOIN paid ON paid.month = k.month AND paid.emp_id = k.emp_id
LEFT JOIN emd  ON emd.month  = k.month AND emd.emp_id  = k.emp_id
LEFT JOIN cur  ON cur.emp_id = k.emp_id
JOIN warehouse.dim_department dp ON dp.department_key = COALESCE(emd.department_key, cur.department_key, 0)
GROUP BY k.month, dp.plant_name, dp.dept_name
ORDER BY k.month, dp.plant_name, dp.dept_name;
