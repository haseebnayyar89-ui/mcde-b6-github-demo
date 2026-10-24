-- Q3: absenteeism rate by plant and month, excluding approved leave
-- rate = Absent days / expected working days (Present + Absent + Missing Punch; leave, holidays, weekly offs excluded)
WITH emd AS (   -- department/plant on the last day of the month (or last working day)
    SELECT m.month, e.emp_id, e.department_key
    FROM warehouse.dim_month m
    JOIN warehouse.dim_employee e
      ON e.hire_date <= m.month_end
     AND (e.separation_date IS NULL OR e.separation_date >= m.month_start)
     AND MIN(m.month_end, COALESCE(e.separation_date, m.month_end)) BETWEEN e.valid_from AND e.valid_to
),
att AS (
    SELECT d.month_key AS month, f.emp_id, f.status
    FROM warehouse.fact_attendance_daily f
    JOIN warehouse.dim_date d ON d.date_key = f.date_key
)
SELECT a.month, dp.plant_name AS plant,
       SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent_days,
       SUM(CASE WHEN a.status IN ('Present', 'Absent', 'Missing Punch') THEN 1 ELSE 0 END) AS expected_working_days,
       ROUND(100.0 * SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN a.status IN ('Present', 'Absent', 'Missing Punch') THEN 1 ELSE 0 END), 0), 2)
             AS absenteeism_rate_pct
FROM att a
JOIN emd ON emd.month = a.month AND emd.emp_id = a.emp_id
JOIN warehouse.dim_department dp ON dp.department_key = emd.department_key
GROUP BY a.month, dp.plant_name
ORDER BY a.month, dp.plant_name;
