-- Stage 4: star schema (SQLite). Foreign keys are enforced (PRAGMA foreign_keys=ON).
-- Row key 0 in each dimension = 'UNKNOWN' so a fact row never loses its dimension.

CREATE TABLE warehouse.dim_department (
    department_key INTEGER PRIMARY KEY,
    dept_id        TEXT NOT NULL UNIQUE,
    dept_name      TEXT,
    plant_code     TEXT,
    plant_name     TEXT,
    cost_center    TEXT,
    previous_name  TEXT,
    renamed_on     TEXT
);

CREATE TABLE warehouse.dim_shift (
    shift_key        INTEGER PRIMARY KEY,
    shift_code       TEXT NOT NULL UNIQUE,
    start_time       TEXT,
    end_time         TEXT,
    crosses_midnight INTEGER,
    grace_minutes    INTEGER
);

CREATE TABLE warehouse.dim_date (
    date_key   INTEGER PRIMARY KEY,           -- YYYYMMDD
    full_date  TEXT NOT NULL UNIQUE,
    year       INTEGER,
    month      INTEGER,
    month_key  TEXT,                          -- YYYY-MM
    month_name TEXT,
    day        INTEGER,
    day_name   TEXT,
    is_sunday  INTEGER,
    week_start TEXT
);

CREATE TABLE warehouse.dim_month (
    month       TEXT PRIMARY KEY,             -- YYYY-MM
    month_start TEXT NOT NULL,
    month_end   TEXT NOT NULL,
    prev_end    TEXT NOT NULL
);

-- SCD Type 2: one row per employee per employment_history record
CREATE TABLE warehouse.dim_employee (
    employee_key             INTEGER PRIMARY KEY,
    emp_id                   TEXT NOT NULL,
    full_name                TEXT,
    gender                   TEXT,
    hire_date                TEXT,
    separation_date          TEXT,
    employment_type          TEXT,
    status                   TEXT,
    annual_leave_entitlement INTEGER,
    department_key           INTEGER NOT NULL REFERENCES dim_department(department_key),
    designation              TEXT,
    grade                    TEXT,
    basic_salary             REAL,
    valid_from               TEXT NOT NULL,
    valid_to                 TEXT NOT NULL,   -- '9999-12-31' = current record
    is_current               INTEGER NOT NULL,
    change_reason            TEXT,
    UNIQUE (emp_id, valid_from)
);
CREATE INDEX warehouse.ix_dim_employee_emp ON dim_employee(emp_id, valid_from);

CREATE TABLE warehouse.fact_attendance_daily (
    attendance_key          INTEGER PRIMARY KEY,
    employee_key            INTEGER NOT NULL REFERENCES dim_employee(employee_key),
    emp_id                  TEXT NOT NULL,
    date_key                INTEGER NOT NULL REFERENCES dim_date(date_key),
    shift_key               INTEGER NOT NULL REFERENCES dim_shift(shift_key),
    department_key          INTEGER NOT NULL REFERENCES dim_department(department_key),
    plant_code              TEXT,
    status                  TEXT NOT NULL,
    check_in                TEXT,
    check_out               TEXT,
    punch_count             INTEGER,
    worked_hours            REAL,
    late_minutes            INTEGER,
    early_departure_minutes INTEGER,
    overtime_hours          REAL,
    is_late                 INTEGER,
    is_early_departure      INTEGER,
    UNIQUE (emp_id, date_key)
);

CREATE TABLE warehouse.fact_leave_day (
    request_id   TEXT NOT NULL,
    date_key     INTEGER NOT NULL REFERENCES dim_date(date_key),
    employee_key INTEGER NOT NULL REFERENCES dim_employee(employee_key),
    emp_id       TEXT NOT NULL,
    leave_type   TEXT,
    PRIMARY KEY (request_id, date_key)
);

CREATE TABLE warehouse.fact_overtime_approved (
    request_id      TEXT PRIMARY KEY,
    employee_key    INTEGER NOT NULL REFERENCES dim_employee(employee_key),
    emp_id          TEXT NOT NULL,
    date_key        INTEGER NOT NULL REFERENCES dim_date(date_key),
    requested_hours REAL,
    approved_hours  REAL,
    status          TEXT,
    approver_id     TEXT
);

CREATE TABLE warehouse.fact_payroll_line (
    line_id        TEXT PRIMARY KEY,
    payroll_month  TEXT NOT NULL,
    employee_key   INTEGER NOT NULL REFERENCES dim_employee(employee_key),
    emp_id         TEXT NOT NULL,
    date_key       INTEGER NOT NULL REFERENCES dim_date(date_key),   -- month-end date
    department_key INTEGER NOT NULL REFERENCES dim_department(department_key),
    component      TEXT,
    component_type TEXT,
    units          REAL,
    amount         REAL
);
