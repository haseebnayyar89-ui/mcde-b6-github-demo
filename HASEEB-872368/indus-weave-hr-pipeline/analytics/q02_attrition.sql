-- Q2: monthly attrition rate by department = separations / average headcount
-- average headcount = (headcount at previous month end + headcount at this month end) / 2
WITH hc_end AS (
    SELECT m.month, e.department_key, COUNT(*) AS hc
    FROM warehouse.dim_month m
    JOIN warehouse.dim_employee e
      ON e.hire_date <= m.month_end
     AND (e.separation_date IS NULL OR e.separation_date > m.month_end)
     AND m.month_end BETWEEN e.valid_from AND e.valid_to
    GROUP BY m.month, e.department_key
),
hc_start AS (
    SELECT m.month, e.department_key, COUNT(*) AS hc
    FROM warehouse.dim_month m
    JOIN warehouse.dim_employee e
      ON e.hire_date <= m.prev_end
     AND (e.separation_date IS NULL OR e.separation_date > m.prev_end)
     AND m.prev_end BETWEEN e.valid_from AND e.valid_to
    GROUP BY m.month, e.department_key
),
seps AS (   -- department on the last working day (= separation_date)
    SELECT m.month, e.department_key, COUNT(*) AS separations
    FROM warehouse.dim_month m
    JOIN warehouse.dim_employee e
      ON e.separation_date BETWEEN m.month_start AND m.month_end
     AND e.separation_date BETWEEN e.valid_from AND e.valid_to
    GROUP BY m.month, e.department_key
),
keys AS (
    SELECT month, department_key FROM hc_end
    UNION SELECT month, department_key FROM hc_start
    UNION SELECT month, department_key FROM seps
)
SELECT k.month, dp.plant_name AS plant, dp.dept_name AS department,
       COALESCE(s.separations, 0) AS separations,
       ROUND((COALESCE(hs.hc, 0) + COALESCE(he.hc, 0)) / 2.0, 2) AS avg_headcount,
       ROUND(100.0 * COALESCE(s.separations, 0)
             / NULLIF((COALESCE(hs.hc, 0) + COALESCE(he.hc, 0)) / 2.0, 0), 2) AS attrition_rate_pct
FROM keys k
JOIN warehouse.dim_department dp ON dp.department_key = k.department_key
LEFT JOIN hc_end he   ON he.month = k.month AND he.department_key = k.department_key
LEFT JOIN hc_start hs ON hs.month = k.month AND hs.department_key = k.department_key
LEFT JOIN seps s      ON s.month  = k.month AND s.department_key  = k.department_key
ORDER BY k.month, dp.plant_name, dp.dept_name;
