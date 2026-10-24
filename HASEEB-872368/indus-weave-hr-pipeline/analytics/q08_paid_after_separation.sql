-- Q8: employees still receiving pay after their separation date
-- separation_date = last day worked, so the separation month itself (final settlement) is not flagged;
-- any EARNING in a later payroll month is.
SELECT e.emp_id, e.full_name, dp.plant_name AS plant, dp.dept_name AS department,
       e.separation_date, f.payroll_month,
       ROUND(SUM(f.amount), 2) AS earnings_paid
FROM warehouse.dim_employee e
JOIN warehouse.fact_payroll_line f ON f.emp_id = e.emp_id AND f.component_type = 'EARNING'
JOIN warehouse.dim_department dp ON dp.department_key = e.department_key
WHERE e.is_current = 1
  AND e.separation_date IS NOT NULL
  AND f.payroll_month > substr(e.separation_date, 1, 7)
GROUP BY e.emp_id, e.full_name, dp.plant_name, dp.dept_name, e.separation_date, f.payroll_month
HAVING SUM(f.amount) > 0
ORDER BY e.emp_id, f.payroll_month;
