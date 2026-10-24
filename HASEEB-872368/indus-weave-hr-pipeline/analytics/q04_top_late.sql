-- Q4: the 10 employees with the most late arrivals (check-in > 10 min after shift start, Present working days)
WITH late AS (
    SELECT f.emp_id, SUM(f.is_late) AS late_arrivals, SUM(f.late_minutes) AS total_late_minutes
    FROM warehouse.fact_attendance_daily f
    GROUP BY f.emp_id
),
ranked AS (
    SELECT emp_id, late_arrivals, total_late_minutes,
           ROW_NUMBER() OVER (ORDER BY late_arrivals DESC, total_late_minutes DESC, emp_id) AS rnk
    FROM late
)
SELECT r.rnk AS rank, r.emp_id, e.full_name, dp.plant_name AS plant, dp.dept_name AS department,
       r.late_arrivals, r.total_late_minutes
FROM ranked r
JOIN warehouse.dim_employee e ON e.emp_id = r.emp_id AND e.is_current = 1
JOIN warehouse.dim_department dp ON dp.department_key = e.department_key
WHERE r.rnk <= 10
ORDER BY r.rnk;
