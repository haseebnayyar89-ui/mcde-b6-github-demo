# Indus Weave HR Pipeline (PeopleOps Data Hackathon)

Python + SQL pipeline: raw exports -> raw -> staging -> warehouse (star schema) -> 10 business answers,
with data quality checks after every load. Database: **SQLite** (allowed by the case study).
Only the Python standard library is used, so **nothing needs to be installed** (Python 3.8+).

Team members: _add names here_

## How to run (clean machine)
1. Put the 13 data files (`employees.csv`, `biometric_punches.csv`, ... `data_dictionary.md`) in a folder named
   `data` next to `run_pipeline.py`, or pass the folder path.
2. Open a terminal in this folder and run:
   ```
   python run_pipeline.py --fresh
   python run_pipeline.py "C:\path\to\data-hackathon-main" --fresh      # if the data is somewhere else
   ```
   (`py run_pipeline.py --fresh` on Windows if `python` is not found.) Runtime is about a minute.
3. Outputs: `analytics/results/q01..q10.csv`, `presentation/cfo_findings.md` (draft with live numbers),
   databases in `db/` (raw.db, staging.db, warehouse.db, pipeline.db with the `dq_results` table).

Running the command again without `--fresh` is safe: the raw load is idempotent (unique `_row_hash`).

## Layout
| Path | Stage |
|---|---|
| `ingestion/ingest_raw.py` | 1 - raw load, all TEXT, `_source_file`, `_loaded_at`, `_row_hash`, row-count log |
| `transform/clean_staging.py` | 2 - typed, cleaned staging tables, rejected rows, cleaning log |
| `transform/sql/03_attendance.sql` | 3 - `staging.attendance_daily` (status, late, early, overtime) |
| `warehouse/ddl/*.sql`, `warehouse/build_warehouse.py`, `warehouse/erd.dbml` | 4 - star schema, SCD2 `dim_employee` |
| `analytics/q01..q10_*.sql`, `analytics/run_queries.py` | 5 - business questions |
| `quality/run_checks.py` | 6 - checks written to `main.dq_results` |
| `run_pipeline.py` | one-command rebuild (bonus) |

## Design decisions and assumptions
* **Schemas**: SQLite has no schemas, so `raw`, `staging` and `warehouse` are three attached database files.
* **Employees**: duplicate `emp_id` -> keep latest `updated_at`; every merge is in `staging.employee_merge_log`.
* **SCD2**: `valid_to` = next record's `effective_from` minus one day; the export's `effective_to` is ignored (rule 2).
  Month figures use the version valid on the month's last day, or the separation date if the employee left (rule 3).
* **Device clock drift**: for each device and month, the median first-punch offset against the rostered shift start
  (non-night shifts) is compared with the median across devices. A gap of 30+ minutes flags the device and its
  punches are shifted by the rounded gap (`staging.device_clock_check`).
* **Duplicate punches**: a punch within 120 seconds of the same employee's previous punch is rejected.
* **Night shifts**: a punch before (previous shift end + 5 hours) belongs to the previous shift date (rule 7).
* **Late / early**: only on `Present` working days, more than 10 minutes; `late_minutes` is the full minutes after start.
* **Absenteeism rate** = Absent days / (Present + Absent + Missing Punch days); leave, holidays and weekly offs are excluded.
* **Attrition** = separations in the month / average of previous and current month-end headcount, per department.
* **Q6** compares paid vs computed overtime per department over the six months together.
* **Q7** "zero attendance" = no punches at all in that month; "paid" = EARNING lines > 0.
* **Q8** flags EARNING in any payroll month after the month of `separation_date` (the last-day-worked month is allowed).
* **Reconciliation**: raw rows = staging rows + `staging.rejected_rows` (or `staging.rejected_punches`).
* Bonus done: `run_pipeline.py`. Not done: incremental load, recruitment funnel, dashboard.
