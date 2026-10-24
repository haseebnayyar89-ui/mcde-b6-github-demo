"""Stage 4: create the star schema (DDL) and load it from staging."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from common import add_days, date_range, run_sql_file

DDL_DIR = Path(__file__).resolve().parent / "ddl"


def run(conn):
    print("Stage 4 - building warehouse star schema")
    conn.commit()
    conn.execute("PRAGMA foreign_keys=OFF")        # allow dropping old tables in any order
    old = conn.execute("SELECT type, name FROM warehouse.sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
    for kind, name in old:
        if kind in ("table", "view"):
            conn.execute(f"DROP {kind.upper()} IF EXISTS warehouse.{name}")
    conn.commit()
    run_sql_file(conn, DDL_DIR / "01_create_tables.sql")
    conn.execute("PRAGMA foreign_keys=ON")         # enforce keys while loading

    names = ["", "January", "February", "March", "April", "May", "June", "July", "August",
             "September", "October", "November", "December"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    rows = []
    for d in date_range("2026-01-01", "2027-06-30"):
        dt = date.fromisoformat(d)
        wk = (dt.fromordinal(dt.toordinal() - dt.weekday())).isoformat()
        rows.append((int(d.replace("-", "")), d, dt.year, dt.month, d[:7], names[dt.month], dt.day,
                     days[dt.weekday()], 1 if dt.weekday() == 6 else 0, wk))
    conn.executemany("INSERT INTO warehouse.dim_date VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    months = []
    for m in config.MONTHS:
        start = m + "-01"
        end = add_days(f"{int(m[:4]) + (1 if m[5:] == '12' else 0)}-{(int(m[5:]) % 12) + 1:02d}-01", -1)
        months.append((m, start, end, add_days(start, -1)))
    conn.executemany("INSERT INTO warehouse.dim_month VALUES (?,?,?,?)", months)
    conn.commit()

    run_sql_file(conn, DDL_DIR / "02_load.sql")
    conn.commit()
    for t in ("dim_employee", "dim_department", "dim_shift", "dim_date", "fact_attendance_daily",
              "fact_leave_day", "fact_overtime_approved", "fact_payroll_line"):
        n = conn.execute(f"SELECT COUNT(*) FROM warehouse.{t}").fetchone()[0]
        print(f"  warehouse.{t:<24} {n:>9,} rows")
