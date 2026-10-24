-- Load dimensions and facts from staging. dim_date and dim_month are loaded by build_warehouse.py.

INSERT INTO warehouse.dim_department VALUES (0, 'UNKNOWN', 'Unknown', 'NA', 'Unknown', NULL, NULL, NULL);
INSERT INTO warehouse.dim_department (dept_id, dept_name, plant_code, plant_name, cost_center, previous_name, renamed_on)
SELECT dept_id, dept_name, plant_code, plant_name, cost_center, previous_name, renamed_on
FROM staging.departments ORDER BY dept_id;

INSERT INTO warehouse.dim_shift VALUES (0, 'UNKNOWN', NULL, NULL, 0, 0);
INSERT INTO warehouse.dim_shift (shift_code, start_time, end_time, crosses_midnight, grace_minutes)
SELECT shift_code, start_time, end_time, crosses_midnight, grace_minutes FROM staging.shifts ORDER BY shift_code;

-- SCD2 employee dimension
INSERT INTO warehouse.dim_employee (employee_key, emp_id, full_name, department_key, valid_from, valid_to, is_current)
VALUES (0, 'UNKNOWN', 'Unknown', 0, '1900-01-01', '1900-01-01', 0);

INSERT INTO warehouse.dim_employee
    (emp_id, full_name, gender, hire_date, separation_date, employment_type, status, annual_leave_entitlement,
     department_key, designation, grade, basic_salary, valid_from, valid_to, is_current, change_reason)
SELECT e.emp_id, e.full_name, e.gender, e.hire_date, e.separation_date, e.employment_type, e.status,
       e.annual_leave_entitlement, COALESCE(dd.department_key, 0), h.designation, h.grade, h.basic_salary,
       h.valid_from, h.valid_to, CASE WHEN h.valid_to = '9999-12-31' THEN 1 ELSE 0 END, h.change_reason
FROM staging.employment_history h
JOIN staging.employees e ON e.emp_id = h.emp_id
LEFT JOIN warehouse.dim_department dd ON dd.dept_id = h.dept_id
ORDER BY h.emp_id, h.valid_from;

-- employees that have no history rows get one record from the employees table
INSERT INTO warehouse.dim_employee
    (emp_id, full_name, gender, hire_date, separation_date, employment_type, status, annual_leave_entitlement,
     department_key, designation, grade, basic_salary, valid_from, valid_to, is_current, change_reason)
SELECT e.emp_id, e.full_name, e.gender, e.hire_date, e.separation_date, e.employment_type, e.status,
       e.annual_leave_entitlement,
       COALESCE((SELECT dd.department_key FROM warehouse.dim_department dd
                 WHERE LOWER(dd.dept_name) = LOWER(e.department) AND dd.plant_code = e.plant_code LIMIT 1), 0),
       e.designation, e.grade, NULL, COALESCE(e.hire_date, '1900-01-01'), '9999-12-31', 1, 'No history record'
FROM staging.employees e
WHERE NOT EXISTS (SELECT 1 FROM staging.employment_history h WHERE h.emp_id = e.emp_id);

-- fact_attendance_daily (employee_key = SCD2 version valid on the work date)
INSERT INTO warehouse.fact_attendance_daily
    (employee_key, emp_id, date_key, shift_key, department_key, plant_code, status, check_in, check_out,
     punch_count, worked_hours, late_minutes, early_departure_minutes, overtime_hours, is_late, is_early_departure)
WITH r AS (
    SELECT a.*,
           COALESCE((SELECT e.employee_key FROM warehouse.dim_employee e
                     WHERE e.emp_id = a.emp_id AND a.work_date BETWEEN e.valid_from AND e.valid_to LIMIT 1),
                    (SELECT e.employee_key FROM warehouse.dim_employee e
                     WHERE e.emp_id = a.emp_id ORDER BY e.valid_from LIMIT 1), 0) AS employee_key
    FROM staging.attendance_daily a
)
SELECT r.employee_key, r.emp_id, CAST(REPLACE(r.work_date, '-', '') AS INTEGER), COALESCE(sh.shift_key, 0),
       e.department_key, r.plant_code, r.status, r.check_in, r.check_out, r.punch_count, r.worked_hours,
       r.late_minutes, r.early_departure_minutes, r.overtime_hours, r.is_late, r.is_early_departure
FROM r
JOIN warehouse.dim_employee e ON e.employee_key = r.employee_key
LEFT JOIN warehouse.dim_shift sh ON sh.shift_code = r.shift_code;

INSERT INTO warehouse.fact_leave_day (request_id, date_key, employee_key, emp_id, leave_type)
SELECT l.request_id, CAST(REPLACE(l.leave_date, '-', '') AS INTEGER),
       COALESCE((SELECT e.employee_key FROM warehouse.dim_employee e
                 WHERE e.emp_id = l.emp_id AND l.leave_date BETWEEN e.valid_from AND e.valid_to LIMIT 1),
                (SELECT e.employee_key FROM warehouse.dim_employee e
                 WHERE e.emp_id = l.emp_id ORDER BY e.valid_from LIMIT 1), 0),
       l.emp_id, l.leave_type
FROM staging.leave_days l
WHERE CAST(REPLACE(l.leave_date, '-', '') AS INTEGER) IN (SELECT date_key FROM warehouse.dim_date);

INSERT INTO warehouse.fact_overtime_approved
    (request_id, employee_key, emp_id, date_key, requested_hours, approved_hours, status, approver_id)
SELECT o.request_id,
       COALESCE((SELECT e.employee_key FROM warehouse.dim_employee e
                 WHERE e.emp_id = o.emp_id AND o.ot_date BETWEEN e.valid_from AND e.valid_to LIMIT 1),
                (SELECT e.employee_key FROM warehouse.dim_employee e
                 WHERE e.emp_id = o.emp_id ORDER BY e.valid_from LIMIT 1), 0),
       COALESCE(o.emp_id, 'UNKNOWN'), CAST(REPLACE(o.ot_date, '-', '') AS INTEGER),
       o.requested_hours, o.approved_hours, o.status, o.approver_id
FROM staging.overtime_requests o
WHERE o.status = 'Approved'                                   -- rule 19
  AND CAST(REPLACE(o.ot_date, '-', '') AS INTEGER) IN (SELECT date_key FROM warehouse.dim_date);

INSERT INTO warehouse.fact_payroll_line
    (line_id, payroll_month, employee_key, emp_id, date_key, department_key, component, component_type, units, amount)
WITH r AS (
    SELECT p.*, date(p.payroll_month || '-01', '+1 month', '-1 day') AS month_end,
           COALESCE((SELECT e.employee_key FROM warehouse.dim_employee e
                     WHERE e.emp_id = p.emp_id
                       AND date(p.payroll_month || '-01', '+1 month', '-1 day') BETWEEN e.valid_from AND e.valid_to LIMIT 1),
                    (SELECT e.employee_key FROM warehouse.dim_employee e
                     WHERE e.emp_id = p.emp_id ORDER BY e.valid_from LIMIT 1), 0) AS employee_key
    FROM staging.payroll_lines p
    WHERE p.payroll_month IS NOT NULL
)
SELECT r.line_id, r.payroll_month, r.employee_key, COALESCE(r.emp_id, 'UNKNOWN'),
       CAST(REPLACE(r.month_end, '-', '') AS INTEGER), e.department_key, r.component, r.component_type,
       r.units, r.amount
FROM r
JOIN warehouse.dim_employee e ON e.employee_key = r.employee_key
WHERE CAST(REPLACE(r.month_end, '-', '') AS INTEGER) IN (SELECT date_key FROM warehouse.dim_date);
