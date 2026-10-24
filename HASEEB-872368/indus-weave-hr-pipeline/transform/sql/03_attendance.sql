-- Stage 3: business logic. Builds staging.attendance_daily (one row per employee per scheduled day).

-- 3a. every employee x every calendar day with the shift they were rostered on (rule 6 already filled)
DROP TABLE IF EXISTS staging.emp_day_shift;
CREATE TABLE staging.emp_day_shift AS
SELECT x.emp_id, x.work_date, x.shift_code, x.dept_id, x.plant_code,
       s.start_time, s.end_time, s.crosses_midnight
FROM (
    SELECT e.emp_id,
           c.cal_date AS work_date,
           COALESCE(rf.shift_code, 'GEN') AS shift_code,
           h.dept_id AS dept_id,
           COALESCE(d.plant_code, e.plant_code) AS plant_code
    FROM staging.employees e
    CROSS JOIN staging.calendar c
    LEFT JOIN staging.roster_filled rf ON rf.emp_id = e.emp_id AND rf.week_start = c.week_start
    LEFT JOIN staging.employment_history h ON h.emp_id = e.emp_id AND c.cal_date BETWEEN h.valid_from AND h.valid_to
    LEFT JOIN staging.departments d ON d.dept_id = h.dept_id
) x
LEFT JOIN staging.shifts s ON s.shift_code = x.shift_code;
CREATE INDEX staging.ix_eds_emp_date ON emp_day_shift(emp_id, work_date);

-- 3b. rule 7: a night-shift punch belongs to the date the shift STARTED.
-- A punch belongs to the previous day when it falls before (previous shift end + 5 hours).
-- For a previous shift that does not cross midnight (e.g. evening overtime past midnight) the punch must also be
-- clearly earlier than today's own check-in window (more than 2 hours before today's shift start).
DROP TABLE IF EXISTS staging.punch_shift_date;
CREATE TABLE staging.punch_shift_date AS
SELECT p.punch_id, p.emp_id, p.punch_ts,
       CASE WHEN prev.work_date IS NOT NULL
                 AND p.punch_ts < datetime(prev.work_date || ' ' || prev.end_time,
                                           CASE WHEN prev.crosses_midnight = 1 THEN '+1 day' ELSE '+0 day' END,
                                           '+5 hours')
                 AND (prev.crosses_midnight = 1
                      OR p.punch_ts < datetime(cur.work_date || ' ' || cur.start_time, '-2 hours'))
            THEN prev.work_date
            ELSE date(p.punch_ts) END AS shift_date
FROM staging.punches p
LEFT JOIN staging.emp_day_shift prev
       ON prev.emp_id = p.emp_id AND prev.work_date = date(p.punch_ts, '-1 day')
LEFT JOIN staging.emp_day_shift cur
       ON cur.emp_id = p.emp_id AND cur.work_date = date(p.punch_ts);

-- 3c. rule 10: check-in = first punch, check-out = last punch per employee per shift date
DROP TABLE IF EXISTS staging.punch_daily;
CREATE TABLE staging.punch_daily AS
SELECT emp_id, shift_date, MIN(punch_ts) AS first_ts, MAX(punch_ts) AS last_ts, COUNT(*) AS n
FROM staging.punch_shift_date
GROUP BY emp_id, shift_date;
CREATE UNIQUE INDEX staging.ix_punch_daily ON punch_daily(emp_id, shift_date);

-- 3d. status, late, early, overtime (rules 12 to 15)
DROP TABLE IF EXISTS staging.attendance_daily;
CREATE TABLE staging.attendance_daily AS
WITH base AS (
    SELECT d.emp_id, d.work_date, d.plant_code, d.dept_id, d.shift_code, d.start_time, d.end_time,
           COALESCE(d.crosses_midnight, 0) AS crosses_midnight,
           CASE WHEN strftime('%w', d.work_date) = '0' THEN 1 ELSE 0 END AS is_sunday,
           CASE WHEN EXISTS (SELECT 1 FROM staging.holidays h
                             WHERE h.holiday_date = d.work_date AND (h.scope = 'ALL' OR h.scope = d.plant_code))
                THEN 1 ELSE 0 END AS is_holiday,
           CASE WHEN EXISTS (SELECT 1 FROM staging.leave_days l
                             WHERE l.emp_id = d.emp_id AND l.leave_date = d.work_date)
                THEN 1 ELSE 0 END AS on_leave,
           COALESCE(p.n, 0) AS punch_count, p.first_ts, p.last_ts
    FROM staging.emp_day_shift d
    JOIN staging.employees e ON e.emp_id = d.emp_id
    LEFT JOIN staging.punch_daily p ON p.emp_id = d.emp_id AND p.shift_date = d.work_date
    WHERE d.work_date BETWEEN MAX(COALESCE(e.hire_date, '1900-01-01'), '@PERIOD_START@')
                          AND MIN(COALESCE(e.separation_date, '9999-12-31'), '@PERIOD_END@')
),
st AS (
    SELECT base.*,
           CASE WHEN is_sunday = 1 AND punch_count = 0 THEN 'Weekly Off'
                WHEN is_holiday = 1 AND punch_count = 0 THEN 'Holiday'
                WHEN on_leave = 1 THEN 'On Leave'
                WHEN punch_count >= 2 THEN 'Present'
                WHEN punch_count = 1 THEN 'Missing Punch'
                ELSE 'Absent' END AS status,
           datetime(work_date || ' ' || start_time) AS start_ts,
           CASE WHEN crosses_midnight = 1 THEN datetime(work_date || ' ' || end_time, '+1 day')
                ELSE datetime(work_date || ' ' || end_time) END AS end_ts
    FROM base
),
m AS (
    SELECT st.*,
           CAST(strftime('%s', first_ts) AS INTEGER) - CAST(strftime('%s', start_ts) AS INTEGER) AS late_secs,
           CAST(strftime('%s', end_ts) AS INTEGER) - CAST(strftime('%s', last_ts) AS INTEGER) AS early_secs,
           CAST(strftime('%s', last_ts) AS INTEGER) - CAST(strftime('%s', end_ts) AS INTEGER) AS after_end_secs,
           CAST(strftime('%s', last_ts) AS INTEGER) - CAST(strftime('%s', first_ts) AS INTEGER) AS span_secs
    FROM st
)
SELECT emp_id, work_date, plant_code, dept_id, shift_code, status,
       first_ts AS check_in, last_ts AS check_out, punch_count, is_sunday, is_holiday,
       CASE WHEN punch_count >= 2 THEN ROUND(span_secs / 3600.0, 2) ELSE 0 END AS worked_hours,
       CASE WHEN status = 'Present' AND is_sunday = 0 AND is_holiday = 0 AND late_secs > @GRACE_SECS@
            THEN late_secs / 60 ELSE 0 END AS late_minutes,
       CASE WHEN status = 'Present' AND is_sunday = 0 AND is_holiday = 0 AND early_secs > @GRACE_SECS@
            THEN early_secs / 60 ELSE 0 END AS early_departure_minutes,
       CASE WHEN status <> 'Present' THEN 0.0
            WHEN is_sunday = 1 OR is_holiday = 1 THEN ((span_secs / 60) / 30) * 0.5
            WHEN after_end_secs >= 1800 THEN ((after_end_secs / 60) / 30) * 0.5
            ELSE 0.0 END AS overtime_hours,
       CASE WHEN status = 'Present' AND is_sunday = 0 AND is_holiday = 0 AND late_secs > @GRACE_SECS@
            THEN 1 ELSE 0 END AS is_late,
       CASE WHEN status = 'Present' AND is_sunday = 0 AND is_holiday = 0 AND early_secs > @GRACE_SECS@
            THEN 1 ELSE 0 END AS is_early_departure
FROM m;
CREATE UNIQUE INDEX staging.ix_att_emp_date ON attendance_daily(emp_id, work_date);
