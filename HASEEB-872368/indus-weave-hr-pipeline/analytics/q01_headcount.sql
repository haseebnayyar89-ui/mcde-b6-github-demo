-- Q1: month-end headcount by plant and department (rule 4; department on the last day of the month, rule 3)
SELECT m.month,
       dp.plant_name AS plant,
       dp.dept_name  AS department,
       COUNT(DISTINCT e.emp_id) AS headcount
FROM warehouse.dim_month m
JOIN warehouse.dim_employee e
  ON e.hire_date <= m.month_end
 AND (e.separation_date IS NULL OR e.separation_date > m.month_end)
 AND m.month_end BETWEEN e.valid_from AND e.valid_to
JOIN warehouse.dim_department dp ON dp.department_key = e.department_key
GROUP BY m.month, dp.plant_name, dp.dept_name
ORDER BY m.month, dp.plant_name, dp.dept_name;
