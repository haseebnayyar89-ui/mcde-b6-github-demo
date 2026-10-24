"""Stage 1: load every file into the raw schema exactly as delivered (all columns TEXT).

* adds _source_file, _loaded_at, _row_hash to every table
* idempotent: _row_hash is UNIQUE and rows are inserted with INSERT OR IGNORE
* logs rows in file vs rows in table to raw._load_log and checks they match
"""
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from common import json_items, row_hash


def read_csv_rows(path):
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(path, newline="", encoding=enc) as f:
                return [r for r in csv.reader(f)]
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Cannot decode {path}")


def _finish(conn, table, fname, n_file, loaded_at):
    n_table = conn.execute(
        f'SELECT COUNT(*) FROM raw."{table}" WHERE _source_file = ?', (fname,)
    ).fetchone()[0]
    status = "MATCH" if n_file == n_table else "MISMATCH"
    conn.execute(
        "INSERT INTO raw._load_log VALUES (?,?,?,?,?,?)",
        (fname, table, n_file, n_table, status, loaded_at),
    )
    conn.commit()
    print(f"  raw.{table:<20} file rows={n_file:>8,}  table rows={n_table:>8,}  {status}")
    return status == "MATCH"


def ingest_csv(conn, table, path, loaded_at):
    rows = read_csv_rows(path)
    header = [h.strip() for h in rows[0]]
    data = [r for r in rows[1:] if any(c.strip() for c in r)]
    n = len(header)
    cols_sql = ", ".join(f'"{h}" TEXT' for h in header)
    conn.execute(
        f'CREATE TABLE IF NOT EXISTS raw."{table}" ({cols_sql}, '
        f"_source_file TEXT, _loaded_at TEXT, _row_hash TEXT UNIQUE)"
    )
    col_list = ", ".join(f'"{h}"' for h in header) + ", _source_file, _loaded_at, _row_hash"
    marks = ",".join("?" * (n + 3))
    fname = Path(path).name
    batch = []
    for i, r in enumerate(data, start=1):
        vals = (r + [""] * n)[:n]
        batch.append(vals + [fname, loaded_at, row_hash(vals, i)])
    conn.executemany(f'INSERT OR IGNORE INTO raw."{table}" ({col_list}) VALUES ({marks})', batch)
    return _finish(conn, table, fname, len(data), loaded_at)


def ingest_json(conn, table, path, loaded_at):
    with open(path, encoding="utf-8-sig") as f:
        items = json_items(json.load(f))
    conn.execute(
        f'CREATE TABLE IF NOT EXISTS raw."{table}" (payload TEXT, '
        f"_source_file TEXT, _loaded_at TEXT, _row_hash TEXT UNIQUE)"
    )
    fname = Path(path).name
    batch = []
    for i, item in enumerate(items, start=1):
        payload = json.dumps(item, ensure_ascii=False)
        batch.append((payload, fname, loaded_at, row_hash([payload], i)))
    conn.executemany(
        f'INSERT OR IGNORE INTO raw."{table}" (payload, _source_file, _loaded_at, _row_hash) '
        f"VALUES (?,?,?,?)",
        batch,
    )
    return _finish(conn, table, fname, len(items), loaded_at)


def run(conn, data_dir):
    print(f"Stage 1 - loading raw files from {data_dir}")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS raw._load_log (file TEXT, table_name TEXT, rows_in_file INTEGER, "
        "rows_in_table INTEGER, status TEXT, loaded_at TEXT)"
    )
    loaded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = True
    for name in config.CSV_FILES:
        path = Path(data_dir) / f"{name}.csv"
        if not path.exists():
            print(f"  WARNING: {path.name} not found - skipped")
            continue
        ok &= ingest_csv(conn, name, path, loaded_at)
    for name in config.JSON_FILES:
        path = Path(data_dir) / f"{name}.json"
        if not path.exists():
            print(f"  WARNING: {path.name} not found - skipped")
            continue
        ok &= ingest_json(conn, name, path, loaded_at)
    return ok


if __name__ == "__main__":
    from common import connect
    c = connect()
    run(c, config.find_data_dir(sys.argv[1] if len(sys.argv) > 1 else None))
