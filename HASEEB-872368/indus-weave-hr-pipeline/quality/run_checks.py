"""Stage 6: automated data quality checks. Results are written to main.dq_results after every load."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ATTENDANCE_STATUSES = ("Present", "Absent", "On Leave", "Holiday", "Weekly Off", "Missing Punch")
PAY_COMPONENTS = ("BASIC", "HOUSE_RENT", "MEDICAL", "CONVEYANCE", "OVERTIME", "INCOME_TAX", "EOBI",
                  "ABSENCE_DEDUCTION", "LOAN_INSTALLMENT")

STAGING_KEYS = {
    "employees": ["emp_id"], "departments": ["dept_id"], "employment_history": ["emp_id", "valid_from"],
    "punches": ["punch_id"], "leave_requests": ["request_id"], "overtime_requests": ["request_id"],
    "payroll_lines": ["line_id"], "attendance_daily": ["emp_id", "work_date"],
}
WAREHOUSE_KEYS = {
    "dim_employee": ["employee_key"], "dim_department": ["department_key"], "dim_shift": ["shift_key"],
    "dim_date": ["date_key"], "dim_month": ["month"], "fact_attendance_daily": ["attendance_key"],
    "fact_leave_day": ["request_id", "date_key"], "fact_overtime_approved": ["request_id"],
    "fact_payroll_line": ["line_id"],
}
FKS = [  # (fact table, fk column, dimension table, dimension key)
    ("fact_attendance_daily", "employee_key", "dim_employee", "employee_key"),
    ("fact_attendance_daily", "date_key", "dim_date", "date_key"),
    ("fact_attendance_daily", "shift_key", "dim_shift", "shift_key"),
    ("fact_attendance_daily", "department_key", "dim_department", "department_key"),
    ("fact_leave_day", "employee_key", "dim_employee", "employee_key"),
    ("fact_leave_day", "date_key", "dim_date", "date_key"),
    ("fact_overtime_approved", "employee_key", "dim_employee", "employee_key"),
    ("fact_overtime_approved", "date_key", "dim_date", "date_key"),
    ("fact_payroll_line", "employee_key", "dim_employee", "employee_key"),
    ("fact_payroll_line", "date_key", "dim_date", "date_key"),
    ("fact_payroll_line", "department_key", "dim_department", "department_key"),
    ("dim_employee", "department_key", "dim_department", "department_key"),
]


class Checker:
    def __init__(self, conn, layer, run_id):
        self.conn, self.layer, self.run_id = conn, layer, run_id
        self.results = []
        conn.execute(
            "CREATE TABLE IF NOT EXISTS main.dq_results (run_id TEXT, checked_at TEXT, layer TEXT, check_type TEXT, "
            "check_name TEXT, table_name TEXT, expected TEXT, actual TEXT, status TEXT, details TEXT)"
        )

    def q(self, sql):
        return self.conn.execute(sql).fetchone()[0]

    def record(self, ctype, name, table, expected, actual, ok, details=""):
        status = "PASS" if ok else "FAIL"
        self.results.append(status)
        self.conn.execute(
            "INSERT INTO main.dq_results VALUES (?,?,?,?,?,?,?,?,?,?)",
            (self.run_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.layer, ctype, name, table,
             str(expected), str(actual), status, details),
        )

    def expect_zero(self, ctype, name, table, sql, details=""):
        n = self.q(sql)
        self.record(ctype, name, table, 0, n, n == 0, details)

    def keys(self, schema, tables):
        for t, cols in tables.items():
            full = f"{schema}.{t}"
            null_cond = " OR ".join(f"{c} IS NULL" for c in cols)
            self.expect_zero("not_null", f"PK not null: {','.join(cols)}", full,
                             f"SELECT COUNT(*) FROM {full} WHERE {null_cond}")
            grp = ",".join(cols)
            self.expect_zero("unique", f"PK unique: {grp}", full,
                             f"SELECT COUNT(*) FROM (SELECT 1 FROM {full} GROUP BY {grp} HAVING COUNT(*) > 1)")


def check_raw(c):
    for file, table, n_file, n_table, status in c.conn.execute(
            "SELECT file, table_name, rows_in_file, rows_in_table, status FROM raw._load_log "
            "WHERE rowid IN (SELECT MAX(rowid) FROM raw._load_log GROUP BY file)").fetchall():
        c.record("row_count", "rows in file = rows in raw table", f"raw.{table}", n_file, n_table,
                 n_file == n_table, file)
    for (t,) in c.conn.execute("SELECT name FROM raw.sqlite_master WHERE type='table' AND name NOT LIKE '\\_%' ESCAPE '\\'"):
        dup = c.q(f'SELECT COUNT(*) - COUNT(DISTINCT _row_hash) FROM raw."{t}"')
        c.record("unique", "_row_hash unique (idempotent load)", f"raw.{t}", 0, dup, dup == 0)


def check_staging(c):
    c.keys("staging", STAGING_KEYS)
    # reconciliation: raw = staging + rejected
    recon = [("employees", "employees"), ("employment_history", "employment_history"),
             ("departments", "departments"), ("shift_roster", "shift_roster"),
             ("device_mapping", "device_mapping"), ("holidays", "holidays"),
             ("overtime_requests", "overtime_requests"), ("payroll_lines", "payroll_lines"),
             ("leave_requests", "leave_requests"), ("shifts", "shifts"), ("applications", "applications")]
    for raw_t, stg_t in recon:
        try:
            raw_n = c.q(f'SELECT COUNT(*) FROM raw."{raw_t}"')
        except Exception:
            continue
        stg_n = c.q(f"SELECT COUNT(*) FROM staging.{stg_t}")
        rej_n = c.q(f"SELECT COUNT(*) FROM staging.rejected_rows WHERE source_table = '{raw_t}'")
        c.record("reconciliation", "raw rows = staging rows + rejected rows", f"staging.{stg_t}", raw_n,
                 stg_n + rej_n, raw_n == stg_n + rej_n, f"staging={stg_n}, rejected={rej_n}")
    raw_n = c.q('SELECT COUNT(*) FROM raw."biometric_punches"')
    stg_n = c.q("SELECT COUNT(*) FROM staging.punches")
    rej_n = c.q("SELECT COUNT(*) FROM staging.rejected_punches")
    c.record("reconciliation", "raw rows = staging rows + rejected rows", "staging.punches", raw_n, stg_n + rej_n,
             raw_n == stg_n + rej_n, f"staging={stg_n}, rejected_punches={rej_n}")
    # accepted values
    bad = c.q("SELECT COUNT(*) FROM staging.attendance_daily WHERE status NOT IN (%s)"
              % ",".join(f"'{s}'" for s in ATTENDANCE_STATUSES))
    c.record("accepted_values", "attendance status in the six allowed values", "staging.attendance_daily", 0, bad, bad == 0)
    bad = c.q("SELECT COUNT(*) FROM staging.payroll_lines WHERE component NOT IN (%s) OR component IS NULL"
              % ",".join(f"'{s}'" for s in PAY_COMPONENTS))
    c.record("accepted_values", "pay component in allowed list", "staging.payroll_lines", 0, bad, bad == 0)
    bad = c.q("SELECT COUNT(*) FROM staging.payroll_lines WHERE component_type NOT IN ('EARNING','DEDUCTION') "
              "OR component_type IS NULL")
    c.record("accepted_values", "component_type is EARNING or DEDUCTION", "staging.payroll_lines", 0, bad, bad == 0)
    bad = c.q("SELECT COUNT(*) FROM staging.leave_days WHERE leave_type IS NULL OR leave_type = '' "
              "OR leave_type <> TRIM(leave_type)")
    types = ", ".join(r[0] for r in c.conn.execute("SELECT DISTINCT leave_type FROM staging.leave_days ORDER BY 1") if r[0])
    c.record("accepted_values", "leave type present and clean", "staging.leave_days", 0, bad, bad == 0, f"types: {types}")
    bad = c.q("SELECT COUNT(*) FROM staging.overtime_requests WHERE status NOT IN ('Approved','Rejected','Pending') "
              "OR status IS NULL")
    c.record("accepted_values", "overtime status in Approved/Rejected/Pending", "staging.overtime_requests", 0, bad, bad == 0)
    # business sanity
    c.expect_zero("sanity", "no negative worked hours", "staging.attendance_daily",
                  "SELECT COUNT(*) FROM staging.attendance_daily WHERE worked_hours < 0")
    c.expect_zero("sanity", "no shift longer than 16 hours", "staging.attendance_daily",
                  "SELECT COUNT(*) FROM staging.attendance_daily WHERE worked_hours > 16")
    c.expect_zero("sanity", "check-out not before check-in", "staging.attendance_daily",
                  "SELECT COUNT(*) FROM staging.attendance_daily WHERE check_out < check_in")
    c.expect_zero("sanity", "no overlapping SCD2 ranges", "staging.employment_history",
                  "SELECT COUNT(*) FROM staging.employment_history a JOIN staging.employment_history b "
                  "ON a.emp_id = b.emp_id AND a.valid_from < b.valid_from AND b.valid_from <= a.valid_to")
    c.expect_zero("sanity", "no duplicate punches within 2 minutes remain", "staging.punches",
                  "SELECT COUNT(*) FROM (SELECT (strftime('%s', punch_ts) - strftime('%s', LAG(punch_ts) OVER "
                  "(PARTITION BY emp_id ORDER BY punch_ts))) AS gap FROM staging.punches) WHERE gap <= 120")


def check_warehouse(c):
    c.keys("warehouse", WAREHOUSE_KEYS)
    for fact, fk, dim, dk in FKS:
        c.expect_zero("referential_integrity", f"{fact}.{fk} has a matching {dim}", f"warehouse.{fact}",
                      f"SELECT COUNT(*) FROM warehouse.{fact} f LEFT JOIN warehouse.{dim} d ON d.{dk} = f.{fk} "
                      f"WHERE d.{dk} IS NULL")
    pairs = [("fact_attendance_daily", "staging.attendance_daily"), ("fact_leave_day", "staging.leave_days"),
             ("fact_payroll_line", "staging.payroll_lines")]
    for fact, stg in pairs:
        a, b = c.q(f"SELECT COUNT(*) FROM {stg}"), c.q(f"SELECT COUNT(*) FROM warehouse.{fact}")
        c.record("reconciliation", "staging rows = fact rows", f"warehouse.{fact}", a, b, a == b)
    a = c.q("SELECT COUNT(*) FROM staging.overtime_requests WHERE status = 'Approved'")
    b = c.q("SELECT COUNT(*) FROM warehouse.fact_overtime_approved")
    c.record("reconciliation", "approved staging rows = fact rows", "warehouse.fact_overtime_approved", a, b, a == b)
    bad = c.q("SELECT COUNT(*) FROM warehouse.fact_attendance_daily WHERE status NOT IN (%s)"
              % ",".join(f"'{s}'" for s in ATTENDANCE_STATUSES))
    c.record("accepted_values", "attendance status in the six allowed values", "warehouse.fact_attendance_daily", 0, bad, bad == 0)
    c.expect_zero("sanity", "no negative worked hours", "warehouse.fact_attendance_daily",
                  "SELECT COUNT(*) FROM warehouse.fact_attendance_daily WHERE worked_hours < 0")
    c.expect_zero("sanity", "no shift longer than 16 hours", "warehouse.fact_attendance_daily",
                  "SELECT COUNT(*) FROM warehouse.fact_attendance_daily WHERE worked_hours > 16")
    c.expect_zero("sanity", "no overlapping SCD2 ranges", "warehouse.dim_employee",
                  "SELECT COUNT(*) FROM warehouse.dim_employee a JOIN warehouse.dim_employee b "
                  "ON a.emp_id = b.emp_id AND a.valid_from < b.valid_from AND b.valid_from <= a.valid_to "
                  "WHERE a.emp_id <> 'UNKNOWN'")
    c.expect_zero("sanity", "exactly one current record per employee", "warehouse.dim_employee",
                  "SELECT COUNT(*) FROM (SELECT emp_id FROM warehouse.dim_employee WHERE emp_id <> 'UNKNOWN' "
                  "GROUP BY emp_id HAVING SUM(is_current) <> 1)")


def run(conn, layer, run_id=None):
    run_id = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    c = Checker(conn, layer, run_id)
    {"raw": check_raw, "staging": check_staging, "warehouse": check_warehouse}[layer](c)
    conn.commit()
    passed, failed = c.results.count("PASS"), c.results.count("FAIL")
    print(f"  data quality [{layer}]: {passed} passed, {failed} failed  (details in main.dq_results)")
    for row in conn.execute("SELECT table_name, check_name, expected, actual, details FROM main.dq_results "
                            "WHERE run_id = ? AND layer = ? AND status = 'FAIL'", (run_id, layer)):
        print(f"    FAIL {row[0]}: {row[1]} (expected {row[2]}, got {row[3]}) {row[4]}")
    return failed == 0
