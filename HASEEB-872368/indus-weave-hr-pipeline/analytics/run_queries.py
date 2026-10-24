"""Stage 5: run every analytics/qNN_*.sql file and save its result as a CSV in analytics/results/."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config

HERE = Path(__file__).resolve().parent


def run(conn):
    print("Stage 5 - running the 10 business queries")
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for sql_file in sorted(HERE.glob("q[0-9][0-9]_*.sql")):
        cur = conn.execute(sql_file.read_text(encoding="utf-8"))
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        out = config.RESULTS_DIR / (sql_file.stem + ".csv")
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        print(f"  {sql_file.name:<52} -> {len(rows):>6,} rows")
