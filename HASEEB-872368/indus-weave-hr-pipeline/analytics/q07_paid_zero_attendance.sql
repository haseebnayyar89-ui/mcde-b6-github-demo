-- Q7: employees paid in a month with zero attendance in that month
-- paid = EARNING lines add up to more than 0; attendance = at least one punch on any day of that month
WITH paid AS (
    SELECT f.payroll_month AS month, f.emp_id, SUM(f.amount) AS earnings
    FROM warehouse.fact_payroll_line f
    WHERE f.component_type = 'EARNING'
    GROUP BY f.payroll_month, f.emp_id
    HAVING SUM(f.amount) > 0
),
att AS (
    SELECT d.month_key AS month, f.emp_id,
           SUM(CASE WHEN f.punch_count > 0 THEN 1 ELSE 0 END) AS attended_days,
           SUM(CASE WHEN f.status = 'On Leave' THEN 1 ELSE 0 END) AS leave_days
    FROM warehouse.fact_attendance_daily f JOIN warehouse.dim_date d ON d.date_key = f.date_key
    GROUP BY d.month_key, f.emp_id
)
SELECT p.month, p.emp_id, e.full_name, dp.plant_name AS plant, dp.dept_name AS department,
       ROUND(p.earnings, 2) AS earnings_paid,
       COALESCE(a.attended_days, 0) AS attended_days,
       COALESCE(a.leave_days, 0) AS approved_leave_days
FROM paid p
LEFT JOIN att a ON a.month = p.month AND a.emp_id = p.emp_id
JOIN warehouse.dim_employee e ON e.emp_id = p.emp_id AND e.is_current = 1
JOIN warehouse.dim_department dp ON dp.department_key = e.department_key
WHERE COALESCE(a.attended_days, 0) = 0
ORDER BY p.month, p.emp_id;
