"""Shared helpers: database connection, cleaning and parsing functions."""
import hashlib
import json
import re
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import config

SCHEMAS = ("raw", "staging", "warehouse")


# ---------------------------------------------------------------- database
def check_sqlite():
    v = tuple(int(x) for x in sqlite3.sqlite_version.split("."))
    if v < (3, 25, 0):
        raise RuntimeError(
            f"SQLite {sqlite3.sqlite_version} is too old (window functions need 3.25+). "
            "Please install Python 3.8 or newer."
        )


def connect():
    """One connection: main = pipeline.db (dq_results), plus attached raw / staging / warehouse."""
    config.DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(config.DB_DIR / "pipeline.db"))
    conn.execute("PRAGMA synchronous=OFF")
    for s in SCHEMAS:
        conn.execute(f"ATTACH DATABASE ? AS {s}", (str(config.DB_DIR / f"{s}.db"),))
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def run_sql_file(conn, path, extra=None):
    text = Path(path).read_text(encoding="utf-8")
    params = {
        "PERIOD_START": config.PERIOD_START,
        "PERIOD_END": config.PERIOD_END,
        "GRACE_SECS": str(config.GRACE_MINUTES * 60),
    }
    params.update(extra or {})
    for k, v in params.items():
        text = text.replace(f"@{k}@", v)
    conn.executescript(text)


def fetch_dicts(conn, table, schema="raw"):
    """Yield each row of raw.<table> as a dict with lower-case keys."""
    cur = conn.execute(f'SELECT * FROM {schema}."{table}" ORDER BY rowid')
    cols = [c[0].strip().lower() for c in cur.description]
    for row in cur:
        yield dict(zip(cols, row))


# ---------------------------------------------------------------- hashing / json
def row_hash(values, ordinal):
    raw = str(ordinal) + "\x1f" + "\x1f".join("" if v is None else str(v) for v in values)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def json_items(data):
    """Return the list of records inside a JSON document (list, dict-with-list, or dict-of-dicts)."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
        vals = list(data.values())
        if vals and all(isinstance(v, dict) for v in vals):
            return [dict({"_key": k}, **v) for k, v in data.items()]
        return [data]
    return [data]


# ---------------------------------------------------------------- text cleaning
def clean_text(v):
    if v is None:
        return None
    s = " ".join(str(v).split())
    return s if s else None


def norm_id(v):
    s = clean_text(v)
    return s.upper() if s else None


def to_float(v):
    s = clean_text(v)
    if s is None:
        return None
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def to_int(v):
    f = to_float(v)
    return int(f) if f is not None else None


def to_bool(v):
    return str(v).strip().lower() in ("1", "true", "yes", "y", "t")


def plant_code(v):
    s = (clean_text(v) or "").upper()
    if s in config.PLANTS:
        return s
    if "KOR" in s:
        return "KOR"
    if "SITE" in s:
        return "SITE"
    if "FAISAL" in s or "FSD" in s:
        return "FSD"
    if "HEAD" in s or s in ("HO", "HQ"):
        return "HO"
    return s.replace(" ", "")[:10] or None


def norm_shift_code(v):
    s = (clean_text(v) or "").upper()
    for key in ("NIGHT", "DAY", "EVE", "GEN"):
        if s.startswith(key):
            return key
    return s or None


def norm_time(v):
    m = re.search(r"(\d{1,2}):(\d{2})", str(v or ""))
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


# ---------------------------------------------------------------- dates
_ISO_RE = re.compile(r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})(?:[T ]+(\d{1,2}):(\d{2})(?::(\d{2}))?)?")
_DATE_FORMATS = ["%d/%m/%Y", "%d-%b-%Y", "%d-%B-%Y", "%d-%m-%Y", "%Y/%m/%d",
                 "%d %b %Y", "%d.%m.%Y", "%b %d, %Y"]
_TS_FORMATS = ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d-%b-%Y %H:%M:%S",
               "%d-%b-%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M",
               "%d/%m/%Y %I:%M:%S %p", "%d/%m/%Y %I:%M %p"]
_EMPTY = ("", "nan", "none", "null", "nat")


def parse_date(v):
    """Any of the known date formats -> 'YYYY-MM-DD' (or None)."""
    if v is None:
        return None
    s = str(v).strip()
    if s.lower() in _EMPTY:
        return None
    m = _ISO_RE.match(s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            return None
    for candidate in (s, s.split(" ")[0]):
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(candidate, fmt).date().isoformat()
            except ValueError:
                pass
    return None


def parse_ts(v):
    """Any known timestamp format -> 'YYYY-MM-DD HH:MM:SS' (or None)."""
    if v is None:
        return None
    s = str(v).strip()
    if s.lower() in _EMPTY:
        return None
    m = _ISO_RE.match(s)
    if m:
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
        hh = int(m.group(4) or 0)
        mm = int(m.group(5) or 0)
        ss = int(m.group(6) or 0)
        if hh > 23 or mm > 59 or ss > 59:
            return None
        return f"{d.isoformat()} {hh:02d}:{mm:02d}:{ss:02d}"
    for fmt in _TS_FORMATS:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    d = parse_date(s)
    return f"{d} 00:00:00" if d else None


def date_style(v):
    s = (str(v).strip() if v is not None else "")
    if not s:
        return "empty"
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return "YYYY-MM-DD"
    if re.match(r"^\d{1,2}/\d{1,2}/\d{4}", s):
        return "DD/MM/YYYY"
    if re.match(r"^\d{1,2}-[A-Za-z]{3}-\d{4}", s):
        return "DD-Mon-YYYY"
    return "other"


def add_days(d, n):
    return (date.fromisoformat(d) + timedelta(days=n)).isoformat()


def monday_of(d):
    dt = date.fromisoformat(d)
    return (dt - timedelta(days=dt.weekday())).isoformat()


def date_range(start, end):
    cur, last = date.fromisoformat(start), date.fromisoformat(end)
    while cur <= last:
        yield cur.isoformat()
        cur += timedelta(days=1)
