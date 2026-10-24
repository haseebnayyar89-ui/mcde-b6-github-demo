"""Stage 2: build typed, cleaned staging tables from the raw schema.

Python is used where row-by-row logic is clearer (date formats, JSON flattening,
device clock drift). Stage 3 (attendance) is plain SQL in transform/sql/.
"""
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from common import (add_days, clean_text, date_range, date_style, fetch_dicts, json_items,
                    monday_of, norm_id, norm_shift_code, norm_time, parse_date, parse_ts,
                    plant_code, to_bool, to_float, to_int)

REJECTS = []   # (source_table, source_key, reason) collected during the run


def recreate(conn, name, cols):
    conn.execute(f"DROP TABLE IF EXISTS staging.{name}")
    conn.execute(f"CREATE TABLE staging.{name} ({cols})")


def insert(conn, name, rows, n_cols):
    marks = ",".join("?" * n_cols)
    conn.executemany(f"INSERT INTO staging.{name} VALUES ({marks})", rows)


def log_issue(conn, table, issue, count, detail=""):
    conn.execute("INSERT INTO staging.cleaning_log VALUES (?,?,?,?)", (table, issue, int(count), detail))


def reject(table, key, reason):
    REJECTS.append((table, str(key), reason))


def keep_first(rows, key_fn, table, key_label):
    """Keep first row per key, reject later duplicates."""
    seen, out = set(), []
    for r in rows:
        k = key_fn(r)
        if k in seen:
            reject(table, k, f"DUPLICATE_{key_label}")
            continue
        seen.add(k)
        out.append(r)
    return out


# ------------------------------------------------------------------ departments
def build_departments(conn):
    rows = []
    name_map = {}
    for d in fetch_dicts(conn, "departments"):
        did = norm_id(d.get("dept_id"))
        if not did:
            reject("departments", d.get("dept_name"), "MISSING_DEPT_ID")
            continue
        name = clean_text(d.get("dept_name"))
        prev = clean_text(d.get("previous_name"))
        pc = plant_code(d.get("plant"))
        rows.append((did, name, pc, config.PLANTS.get(pc, clean_text(d.get("plant"))),
                     clean_text(d.get("cost_center")), prev, parse_date(d.get("renamed_on"))))
        if name:
            name_map[name.lower()] = name
        if prev and name:
            name_map[prev.lower()] = name
    rows = keep_first(rows, lambda r: r[0], "departments", "DEPT_ID")
    recreate(conn, "departments", "dept_id TEXT PRIMARY KEY, dept_name TEXT, plant_code TEXT, plant_name TEXT, "
                                  "cost_center TEXT, previous_name TEXT, renamed_on TEXT")
    insert(conn, "departments", rows, 7)
    log_issue(conn, "departments", "departments renamed mid-period (previous_name filled)",
              sum(1 for r in rows if r[5]), "old names are mapped to the new name")
    dept_plant = {r[0]: r[2] for r in rows}
    return name_map, dept_plant


# ------------------------------------------------------------------ employees
def build_employees(conn, name_map):
    best, total = {}, 0
    merge_log = []
    for i, d in enumerate(fetch_dicts(conn, "employees")):
        total += 1
        emp = norm_id(d.get("emp_id"))
        if not emp:
            reject("employees", i, "MISSING_EMP_ID")
            continue
        upd = parse_ts(d.get("updated_at")) or "0000-00-00 00:00:00"
        cand = (upd, i, d)
        if emp in best:
            old = best[emp]
            if (cand[0], cand[1]) > (old[0], old[1]):
                kept, dropped = cand, old
            else:
                kept, dropped = old, cand
            best[emp] = kept
            merge_log.append((emp, kept[0], dropped[0], "Duplicate emp_id: kept row with latest updated_at"))
            reject("employees", emp, "DUPLICATE_EMP_ID_OLDER_UPDATED_AT")
        else:
            best[emp] = cand

    styles, bad_dates, dept_fixed = Counter(), Counter(), 0
    rows = []
    for emp, (upd, _, d) in sorted(best.items()):
        for col in ("date_of_birth", "hire_date", "separation_date"):
            st = date_style(d.get(col))
            if st != "empty":
                styles[(col, st)] += 1
        dob, hire, sep = (parse_date(d.get(c)) for c in ("date_of_birth", "hire_date", "separation_date"))
        if clean_text(d.get("hire_date")) and not hire:
            bad_dates["hire_date"] += 1
        if clean_text(d.get("separation_date")) and not sep:
            bad_dates["separation_date"] += 1
        raw_dept = d.get("department")
        dept_key = (clean_text(raw_dept) or "").lower()
        dept = name_map.get(dept_key) or (clean_text(raw_dept) or "").title() or None
        if dept != raw_dept:
            dept_fixed += 1
        pc = plant_code(d.get("plant"))
        status = (clean_text(d.get("status")) or "").title() or None
        rows.append((emp, clean_text(d.get("full_name")), clean_text(d.get("gender")),
                     (clean_text(d.get("email")) or "").lower() or None, clean_text(d.get("phone")),
                     dob, hire, sep, pc, dept, clean_text(d.get("designation")),
                     clean_text(d.get("grade")), clean_text(d.get("employment_type")),
                     status, to_int(d.get("annual_leave_entitlement")), upd))
    recreate(conn, "employees",
             "emp_id TEXT PRIMARY KEY, full_name TEXT, gender TEXT, email TEXT, phone TEXT, date_of_birth TEXT, "
             "hire_date TEXT, separation_date TEXT, plant_code TEXT, department TEXT, designation TEXT, grade TEXT, "
             "employment_type TEXT, status TEXT, annual_leave_entitlement INTEGER, updated_at TEXT")
    insert(conn, "employees", rows, 16)
    recreate(conn, "employee_merge_log", "emp_id TEXT, kept_updated_at TEXT, dropped_updated_at TEXT, reason TEXT")
    insert(conn, "employee_merge_log", merge_log, 4)
    log_issue(conn, "employees", "duplicate emp_id rows merged", len(merge_log), "see staging.employee_merge_log")
    for (col, st), n in sorted(styles.items()):
        log_issue(conn, "employees", f"{col}: date format {st}", n, "converted to YYYY-MM-DD")
    for col, n in bad_dates.items():
        log_issue(conn, "employees", f"{col}: unparseable date", n, "set to NULL")
    log_issue(conn, "employees", "department text trimmed / recased / old name mapped", dept_fixed, "")
    return {r[0]: r for r in rows}


# ------------------------------------------------------------------ employment history
def build_history(conn, dept_plant):
    by_emp = defaultdict(list)
    for i, d in enumerate(fetch_dicts(conn, "employment_history")):
        emp, eff = norm_id(d.get("emp_id")), parse_date(d.get("effective_from"))
        if not emp or not eff:
            reject("employment_history", f"{emp}|{d.get('effective_from')}", "MISSING_EMP_OR_EFFECTIVE_FROM")
            continue
        by_emp[emp].append((eff, i, d))
    rows, mismatch_emps = [], set()
    for emp, recs in by_emp.items():
        recs.sort(key=lambda x: (x[0], x[1]))
        kept = []
        for r in recs:                      # same effective_from twice: keep the later row
            if kept and kept[-1][0] == r[0]:
                reject("employment_history", f"{emp}|{r[0]}", "DUPLICATE_EFFECTIVE_FROM")
                kept[-1] = r
            else:
                kept.append(r)
        for j, (eff, _, d) in enumerate(kept):
            valid_to = add_days(kept[j + 1][0], -1) if j + 1 < len(kept) else "9999-12-31"
            exported = parse_date(d.get("effective_to"))
            expected_export = None if valid_to == "9999-12-31" else valid_to
            if exported != expected_export:
                mismatch_emps.add(emp)
            rows.append((emp, eff, valid_to, norm_id(d.get("dept_id")), clean_text(d.get("designation")),
                         clean_text(d.get("grade")), to_float(d.get("basic_salary")),
                         clean_text(d.get("change_reason"))))
    rows.sort()
    recreate(conn, "employment_history",
             "emp_id TEXT, valid_from TEXT, valid_to TEXT, dept_id TEXT, designation TEXT, grade TEXT, "
             "basic_salary REAL, change_reason TEXT, PRIMARY KEY (emp_id, valid_from)")
    insert(conn, "employment_history", rows, 8)
    log_issue(conn, "employment_history", "employees whose exported effective_to was wrong (overlap/gap)",
              len(mismatch_emps), "valid_to recomputed = next effective_from - 1 day (rule 2)")
    hist = defaultdict(list)
    for r in rows:
        hist[r[0]].append((r[1], r[2], dept_plant.get(r[3])))
    return hist


# ------------------------------------------------------------------ shifts / holidays
DEFAULT_SHIFTS = {"DAY": ("06:00", "14:00", 0), "EVE": ("14:00", "22:00", 0),
                  "NIGHT": ("22:00", "06:00", 1), "GEN": ("09:00", "17:00", 0)}


def _pick(d, keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def build_shifts(conn):
    rows = []
    for d in fetch_dicts(conn, "shifts"):
        item = json.loads(d["payload"])
        code = norm_shift_code(_pick(item, ["shift_code", "code", "shift", "shift_id", "id", "name", "_key"]))
        start = norm_time(_pick(item, ["start_time", "start", "shift_start"]))
        end = norm_time(_pick(item, ["end_time", "end", "shift_end"]))
        if not (code and start and end):
            continue
        crosses_raw = _pick(item, ["crosses_midnight", "crosses"])
        crosses = 1 if (to_bool(crosses_raw) or end < start) else 0
        grace = to_int(_pick(item, ["grace_minutes", "grace"])) or 0
        rows.append((code, start, end, crosses, grace))
    rows = keep_first(rows, lambda r: r[0], "shifts", "SHIFT_CODE")
    if len(rows) < 4:
        print("  WARNING: shifts.json could not be fully read - using default shift times")
        have = {r[0] for r in rows}
        for code, (s, e, c) in DEFAULT_SHIFTS.items():
            if code not in have:
                rows.append((code, s, e, c, 10))
        log_issue(conn, "shifts", "default shift times used for missing shifts", 1, "check shifts.json")
    recreate(conn, "shifts", "shift_code TEXT PRIMARY KEY, start_time TEXT, end_time TEXT, "
                             "crosses_midnight INTEGER, grace_minutes INTEGER")
    insert(conn, "shifts", rows, 5)
    return {r[0]: (int(r[1][:2]) * 60 + int(r[1][3:5]), r[3]) for r in rows}


def build_holidays(conn):
    rows = []
    for d in fetch_dicts(conn, "holidays"):
        hd = parse_date(d.get("holiday_date"))
        if not hd:
            reject("holidays", d.get("holiday_date"), "BAD_DATE")
            continue
        scope = (clean_text(d.get("scope")) or "ALL").upper()
        scope = scope if scope == "ALL" else plant_code(scope)
        rows.append((hd, clean_text(d.get("holiday_name")), scope))
    rows = keep_first(rows, lambda r: (r[0], r[2]), "holidays", "HOLIDAY")
    recreate(conn, "holidays", "holiday_date TEXT, holiday_name TEXT, scope TEXT, PRIMARY KEY (holiday_date, scope)")
    insert(conn, "holidays", rows, 3)
    return {(r[0], r[2]) for r in rows}


# ------------------------------------------------------------------ roster
def build_roster(conn, employees):
    rows = []
    for d in fetch_dicts(conn, "shift_roster"):
        emp, ws = norm_id(d.get("emp_id")), parse_date(d.get("week_start"))
        code = norm_shift_code(d.get("shift_code"))
        if not (emp and ws and code):
            reject("shift_roster", f"{emp}|{d.get('week_start')}", "MISSING_EMP_WEEK_OR_SHIFT")
            continue
        rows.append((emp, monday_of(ws), code))
    rows = keep_first(rows, lambda r: (r[0], r[1]), "shift_roster", "EMP_WEEK")
    recreate(conn, "shift_roster", "emp_id TEXT, week_start TEXT, shift_code TEXT, PRIMARY KEY (emp_id, week_start)")
    insert(conn, "shift_roster", rows, 3)

    # rule 6: a missing week = same shift as previous week
    weeks = [w for w in date_range(monday_of(config.PERIOD_START), monday_of(config.PERIOD_END))
             if date.fromisoformat(w).weekday() == 0]
    known = defaultdict(dict)
    for emp, ws, code in rows:
        known[emp][ws] = code
    filled, n_filled = [], 0
    for emp, wk in known.items():
        first_known = wk[min(wk)]
        prev = None
        for w in weeks:
            if w in wk:
                prev = wk[w]
                filled.append((emp, w, prev, 0))
            else:
                prev = prev or first_known
                filled.append((emp, w, prev, 1))
                n_filled += 1
    recreate(conn, "roster_filled", "emp_id TEXT, week_start TEXT, shift_code TEXT, is_filled INTEGER, "
                                    "PRIMARY KEY (emp_id, week_start)")
    insert(conn, "roster_filled", filled, 4)
    log_issue(conn, "shift_roster", "missing roster weeks filled from previous week", n_filled, "rule 6")
    roster = {(e, w): c for e, w, c, _ in filled}
    calendar = [(d, monday_of(d), 1 if date.fromisoformat(d).weekday() == 6 else 0)
                for d in date_range(add_days(config.PERIOD_START, -1), config.PERIOD_END)]
    recreate(conn, "calendar", "cal_date TEXT PRIMARY KEY, week_start TEXT, is_sunday INTEGER")
    insert(conn, "calendar", calendar, 3)
    return roster


# ------------------------------------------------------------------ device mapping + punches
def build_device_mapping(conn):
    rows = []
    for d in fetch_dicts(conn, "device_mapping"):
        dev, usr, emp = clean_text(d.get("device_id")), clean_text(d.get("device_user_id")), norm_id(d.get("emp_id"))
        if not (dev and usr and emp):
            reject("device_mapping", f"{dev}|{usr}", "MISSING_FIELD")
            continue
        rows.append((dev, usr, emp, parse_date(d.get("enrolled_on"))))
    rows = keep_first(rows, lambda r: (r[0], r[1]), "device_mapping", "DEVICE_USER")
    recreate(conn, "device_mapping", "device_id TEXT, device_user_id TEXT, emp_id TEXT, enrolled_on TEXT, "
                                     "PRIMARY KEY (device_id, device_user_id)")
    insert(conn, "device_mapping", rows, 4)
    return {(r[0], r[1]): r[2] for r in rows}


def build_punches(conn, mapping, roster, shift_info):
    rej, good = [], []
    for d in fetch_dicts(conn, "biometric_punches"):
        pid, dev = clean_text(d.get("punch_id")), clean_text(d.get("device_id"))
        usr, raw_ts = clean_text(d.get("device_user_id")), d.get("punch_time")
        emp = mapping.get((dev, usr))
        if emp is None:
            rej.append((pid, dev, usr, raw_ts, "UNMAPPED_DEVICE_USER"))
            continue
        ts = parse_ts(raw_ts)
        if ts is None:
            rej.append((pid, dev, usr, raw_ts, "BAD_TIMESTAMP"))
            continue
        good.append([pid, dev, emp, ts])
    n_unmapped = sum(1 for r in rej if r[4] == "UNMAPPED_DEVICE_USER")

    # ---- device clock drift: median check-in offset vs shift start, per device and month
    first_by_day = {}
    for pid, dev, emp, ts in good:
        k = (emp, ts[:10])
        cur = first_by_day.get(k)
        if cur is None or ts < cur[0]:
            first_by_day[k] = (ts, dev)
    monday_cache, offsets = {}, defaultdict(list)
    for (emp, day), (ts, dev) in first_by_day.items():
        wk = monday_cache.get(day) or monday_cache.setdefault(day, monday_of(day))
        info = shift_info.get(roster.get((emp, wk)))
        if not info or info[1]:               # skip unknown shifts and night shifts
            continue
        minute = int(ts[11:13]) * 60 + int(ts[14:16])
        offsets[(dev, day[:7])].append((minute - info[0] + 720) % 1440 - 720)
    med = {k: statistics.median(v) for k, v in offsets.items() if len(v) >= config.DRIFT_MIN_SAMPLES}
    by_month = defaultdict(list)
    for (dev, mon), m in med.items():
        by_month[mon].append(m)
    corrections, check_rows = {}, []
    for (dev, mon), m in sorted(med.items()):
        devices = by_month[mon]
        overall = statistics.median(devices) if len(devices) >= 2 else m
        diff = m - overall
        flagged = len(devices) >= 2 and abs(diff) >= config.DRIFT_THRESHOLD_MIN
        corr = -int(round(diff / 15.0) * 15) if flagged else 0
        if flagged:
            corrections[(dev, mon)] = corr
        check_rows.append((dev, mon, len(offsets[(dev, mon)]), float(m), float(overall), float(diff),
                           1 if flagged else 0, corr))
    recreate(conn, "device_clock_check", "device_id TEXT, month TEXT, samples INTEGER, median_checkin_offset_min REAL, "
                                         "all_devices_median_min REAL, diff_min REAL, flagged INTEGER, correction_min INTEGER")
    insert(conn, "device_clock_check", check_rows, 8)
    bad_devices = sorted({k[0] for k in corrections})
    log_issue(conn, "biometric_punches", "device clock drift detected", len(bad_devices),
              f"devices={bad_devices}; found by comparing each device's median first-punch offset vs shift start "
              f"(staging.device_clock_check); corrected by the shown minutes")

    adjusted = 0
    for r in good:
        corr = corrections.get((r[1], r[3][:7]))
        r.append(corr or 0)
        if corr:
            r[3] = (datetime.fromisoformat(r[3]) + timedelta(minutes=corr)).strftime("%Y-%m-%d %H:%M:%S")
            adjusted += 1
    log_issue(conn, "biometric_punches", "punches with corrected timestamp", adjusted, "")

    # ---- rule 9: duplicate punches (LAG logic): within 2 minutes of the previous punch of same employee
    good.sort(key=lambda r: (r[2], r[3], r[0] or ""))
    clean, prev_emp, prev_dt, n_dup = [], None, None, 0
    for pid, dev, emp, ts, corr in good:
        dt = datetime.fromisoformat(ts)
        if emp == prev_emp and (dt - prev_dt).total_seconds() <= config.DUP_PUNCH_SECONDS:
            rej.append((pid, dev, None, ts, "DUPLICATE_WITHIN_2_MIN"))
            n_dup += 1
        else:
            clean.append((pid, dev, emp, ts, corr))
        prev_emp, prev_dt = emp, dt
    log_issue(conn, "biometric_punches", "unmapped device users (contractors/visitors) rejected", n_unmapped, "")
    log_issue(conn, "biometric_punches", "duplicate punches within 2 minutes rejected", n_dup, "")

    recreate(conn, "punches", "punch_id TEXT PRIMARY KEY, device_id TEXT, emp_id TEXT, punch_ts TEXT, clock_adjust_min INTEGER")
    insert(conn, "punches", clean, 5)
    conn.execute("CREATE INDEX staging.ix_punches_emp_ts ON punches(emp_id, punch_ts)")
    recreate(conn, "rejected_punches", "punch_id TEXT, device_id TEXT, device_user_id TEXT, punch_time_raw TEXT, reason TEXT")
    insert(conn, "rejected_punches", rej, 5)


# ------------------------------------------------------------------ leave
def _role(step):
    text = f"{step.get('approver_role', '')} {step.get('step', '')}".lower()
    if "manager" in text:
        return "Manager"
    if "hr" in text.split() or "human" in text or " hr" in f" {text}":
        return "HR"
    s = str(step.get("step", "")).strip()
    return {"1": "Manager", "2": "HR"}.get(s, clean_text(step.get("approver_role")) or "Unknown")


def build_leave(conn, employees, hist, holiday_set):
    reqs, steps, days = [], [], []
    seen = set()
    for d in fetch_dicts(conn, "leave_requests"):
        r = json.loads(d["payload"])
        emp_obj = r.get("employee") if isinstance(r.get("employee"), dict) else {}
        leave = r.get("leave") if isinstance(r.get("leave"), dict) else {}
        rid = clean_text(r.get("request_id"))
        if not rid or rid in seen:
            reject("leave_requests", rid, "MISSING_OR_DUPLICATE_REQUEST_ID")
            continue
        seen.add(rid)
        emp = norm_id(emp_obj.get("emp_id") or r.get("emp_id"))
        ltype = (clean_text(leave.get("type") or r.get("leave_type")) or "").title() or None
        frm, to = parse_date(leave.get("from") or r.get("from")), parse_date(leave.get("to") or r.get("to"))
        cancelled = clean_text(r.get("cancelled_at"))
        approvals = r.get("approvals") or []
        actions = {}
        for n, st in enumerate(approvals, start=1):
            role = _role(st)
            action = (clean_text(st.get("action")) or "").title() or None
            steps.append((rid, n, role, clean_text(st.get("approver_id")), action, parse_ts(st.get("acted_at"))))
            actions.setdefault(role, []).append(action)
        mgr_ok = "Approved" in actions.get("Manager", [])
        hr_ok = "Approved" in actions.get("HR", [])
        valid = 1 if (mgr_ok and hr_ok and not cancelled) else 0
        if cancelled:
            status = "Cancelled"
        elif valid:
            status = "Approved"
        elif any(a == "Rejected" for v in actions.values() for a in v):
            status = "Rejected"
        else:
            status = "Pending"
        reqs.append((rid, emp, ltype, frm, to, to_int(leave.get("days_requested")),
                     parse_ts(r.get("submitted_at")), parse_ts(cancelled), status, valid))
        if valid and frm and to and frm <= to and (emp or "") and emp in employees:
            plant_default = employees[emp][8]
            for day in date_range(frm, min(to, add_days(frm, 400))):
                if date.fromisoformat(day).weekday() == 6:
                    continue                                   # rule 17: Sundays are not leave days
                pc = plant_default
                for vf, vt, p in hist.get(emp, []):
                    if vf <= day <= vt and p:
                        pc = p
                if (day, "ALL") in holiday_set or (day, pc) in holiday_set:
                    continue                                   # rule 17: plant holidays are not leave days
                days.append((rid, emp, ltype, day))
    recreate(conn, "leave_requests",
             "request_id TEXT PRIMARY KEY, emp_id TEXT, leave_type TEXT, from_date TEXT, to_date TEXT, "
             "days_requested INTEGER, submitted_at TEXT, cancelled_at TEXT, final_status TEXT, is_valid INTEGER")
    insert(conn, "leave_requests", reqs, 10)
    recreate(conn, "leave_approval_steps", "request_id TEXT, step_no INTEGER, role TEXT, approver_id TEXT, "
                                           "action TEXT, acted_at TEXT")
    insert(conn, "leave_approval_steps", steps, 6)
    recreate(conn, "leave_days", "request_id TEXT, emp_id TEXT, leave_type TEXT, leave_date TEXT, "
                                 "PRIMARY KEY (request_id, leave_date)")
    insert(conn, "leave_days", days, 4)
    conn.execute("CREATE INDEX staging.ix_leave_days_emp ON leave_days(emp_id, leave_date)")
    cnt = Counter(r[8] for r in reqs)
    log_issue(conn, "leave_requests", "requests by final status", len(reqs), json.dumps(dict(cnt)))


# ------------------------------------------------------------------ overtime / payroll / applications
def build_overtime(conn):
    rows = []
    for d in fetch_dicts(conn, "overtime_requests"):
        rid = clean_text(d.get("request_id"))
        rows.append((rid, norm_id(d.get("emp_id")), parse_date(d.get("ot_date")), to_float(d.get("requested_hours")),
                     to_float(d.get("approved_hours")), (clean_text(d.get("status")) or "").title() or None,
                     clean_text(d.get("approver_id")), parse_ts(d.get("requested_at"))))
    rows = keep_first(rows, lambda r: r[0], "overtime_requests", "REQUEST_ID")
    recreate(conn, "overtime_requests", "request_id TEXT PRIMARY KEY, emp_id TEXT, ot_date TEXT, requested_hours REAL, "
                                        "approved_hours REAL, status TEXT, approver_id TEXT, requested_at TEXT")
    insert(conn, "overtime_requests", rows, 8)


def build_payroll(conn):
    rows = []
    for d in fetch_dicts(conn, "payroll_lines"):
        pm = clean_text(d.get("payroll_month")) or ""
        pm = pm[:7] if len(pm) >= 7 and pm[4] == "-" else (parse_date(pm) or "")[:7] or None
        comp = (clean_text(d.get("component")) or "").upper().replace(" ", "_") or None
        ctype = (clean_text(d.get("component_type")) or "").upper() or None
        rows.append((clean_text(d.get("line_id")), pm, norm_id(d.get("emp_id")), comp, ctype,
                     to_float(d.get("units")), to_float(d.get("amount"))))
    rows = keep_first(rows, lambda r: r[0], "payroll_lines", "LINE_ID")
    recreate(conn, "payroll_lines", "line_id TEXT PRIMARY KEY, payroll_month TEXT, emp_id TEXT, component TEXT, "
                                    "component_type TEXT, units REAL, amount REAL")
    insert(conn, "payroll_lines", rows, 7)


def build_applications(conn):
    rows = []
    for d in fetch_dicts(conn, "applications"):
        rows.append((clean_text(d.get("application_id")), clean_text(d.get("candidate_id")),
                     clean_text(d.get("job_req_id")), norm_id(d.get("dept_id")),
                     clean_text(d.get("stage")), parse_date(d.get("stage_date"))))
    recreate(conn, "applications", "application_id TEXT, candidate_id TEXT, job_req_id TEXT, dept_id TEXT, "
                                   "stage TEXT, stage_date TEXT")
    insert(conn, "applications", rows, 6)


# ------------------------------------------------------------------ orchestration
def run(conn):
    print("Stage 2 - cleaning and standardising into staging")
    REJECTS.clear()
    recreate(conn, "cleaning_log", "table_name TEXT, issue TEXT, row_count INTEGER, detail TEXT")
    name_map, dept_plant = build_departments(conn)
    employees = build_employees(conn, name_map)
    hist = build_history(conn, dept_plant)
    shift_info = build_shifts(conn)
    holiday_set = build_holidays(conn)
    roster = build_roster(conn, employees)
    mapping = build_device_mapping(conn)
    build_punches(conn, mapping, roster, shift_info)
    build_leave(conn, employees, hist, holiday_set)
    build_overtime(conn)
    build_payroll(conn)
    build_applications(conn)
    recreate(conn, "rejected_rows", "source_table TEXT, source_key TEXT, reason TEXT")
    insert(conn, "rejected_rows", REJECTS, 3)
    conn.commit()
    for t in ("employees", "employment_history", "punches", "rejected_punches", "leave_days"):
        n = conn.execute(f"SELECT COUNT(*) FROM staging.{t}").fetchone()[0]
        print(f"  staging.{t:<20} {n:>9,} rows")
