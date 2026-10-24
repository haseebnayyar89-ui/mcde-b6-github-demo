"""One command rebuild:  python run_pipeline.py [path-to-data-folder] [--fresh]

Stage 1 raw load -> Stage 2 staging -> Stage 3 attendance -> Stage 4 warehouse -> Stage 5 queries
-> Stage 6 data quality checks after every load -> draft CFO findings.
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import config
import common


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir", nargs="?", help="folder that contains employees.csv and the other data files")
    ap.add_argument("--fresh", action="store_true", help="delete all databases first (full rebuild)")
    args = ap.parse_args()

    common.check_sqlite()
    data_dir = config.find_data_dir(args.data_dir)
    if args.fresh:
        for f in config.DB_DIR.glob("*.db"):
            f.unlink()
    conn = common.connect()
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    t0 = time.time()

    from ingestion import ingest_raw
    from transform import clean_staging
    from warehouse import build_warehouse
    from quality import run_checks
    from analytics import run_queries
    from presentation import make_findings

    ingest_raw.run(conn, data_dir)
    run_checks.run(conn, "raw", run_id)

    clean_staging.run(conn)
    print("Stage 3 - business logic (attendance_daily)")
    common.run_sql_file(conn, Path(__file__).parent / "transform" / "sql" / "03_attendance.sql")
    n = conn.execute("SELECT COUNT(*) FROM staging.attendance_daily").fetchone()[0]
    print(f"  staging.attendance_daily       {n:>9,} rows")
    run_checks.run(conn, "staging", run_id)

    build_warehouse.run(conn)
    run_checks.run(conn, "warehouse", run_id)

    run_queries.run(conn)
    make_findings.run(conn)
    print(f"Done in {time.time() - t0:.0f} seconds. Results: analytics/results/*.csv, "
          f"presentation/cfo_findings.md, table main.dq_results")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
