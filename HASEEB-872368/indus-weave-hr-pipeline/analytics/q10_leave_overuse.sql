-- Q10: employees whose approved Annual leave days in these six months already exceed their full-year entitlement
WITH used AS (
    SELECT l.emp_id, COUNT(DISTINCT d.full_date) AS annual_days_used
    FROM warehouse.fact_leave_day l
    JOIN warehouse.dim_date d ON d.date_key = l.date_key
    WHERE LOWER(l.leave_type) LIKE 'annual%'
      AND d.full_date BETWEEN '2026-04-01' AND '2026-09-30'
    GROUP BY l.emp_id
)
SELECT e.emp_id, e.full_name, dp.plant_name AS plant, dp.dept_name AS department,
       e.annual_leave_entitlement, u.annual_days_used,
       u.annual_days_used - e.annual_leave_entitlement AS days_over_entitlement
FROM used u
JOIN warehouse.dim_employee e ON e.emp_id = u.emp_id AND e.is_current = 1
JOIN warehouse.dim_department dp ON dp.department_key = e.department_key
WHERE u.annual_days_used > e.annual_leave_entitlement
ORDER BY days_over_entitlement DESC, e.emp_id;
