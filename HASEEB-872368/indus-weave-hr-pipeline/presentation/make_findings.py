"""Draft presentation/cfo_findings.md with numbers pulled from the warehouse. Review and edit the wording."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config

OUT = Path(__file__).resolve().parent / "cfo_findings.md"

EVIDENCE_Q3 = """SELECT COUNT(*) AS approved_requests,
       SUM(o.approved_hours) AS approved_hours,
       SUM(CASE WHEN COALESCE(a.overtime_hours, 0) = 0 THEN 1 ELSE 0 END) AS requests_on_days_with_no_ot,
       SUM(CASE WHEN COALESCE(a.overtime_hours, 0) = 0 THEN o.approved_hours ELSE 0 END) AS hours_on_days_with_no_ot
FROM warehouse.fact_overtime_approved o
LEFT JOIN warehouse.fact_attendance_daily a ON a.emp_id = o.emp_id AND a.date_key = o.date_key;"""


def read_csv(name):
    p = config.RESULTS_DIR / f"{name}.csv"
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    return float(x) if x not in (None, "") else 0.0


def run(conn):
    q = lambda sql: conn.execute(sql).fetchone()
    comp = q("SELECT COALESCE(SUM(overtime_hours),0) FROM warehouse.fact_attendance_daily")[0]
    appr = q("SELECT COALESCE(SUM(approved_hours),0) FROM warehouse.fact_overtime_approved")[0]
    paid = q("SELECT COALESCE(SUM(units),0) FROM warehouse.fact_payroll_line WHERE component='OVERTIME'")[0]
    paid_amt = q("SELECT COALESCE(SUM(amount),0) FROM warehouse.fact_payroll_line WHERE component='OVERTIME'")[0]
    def rel(a, b):
        if not b:
            return "n/a"
        d = 100.0 * (a - b) / b
        return f"{abs(d):.1f}% {'above' if d >= 0 else 'below'}"
    q6 = read_csv("q06_paid_ot_gap")[:3]
    top = "; ".join(f"{r['department']} ({r['plant']}): paid {num(r['paid_ot_hours']):,.0f} h vs computed "
                    f"{num(r['computed_ot_hours']):,.0f} h" for r in q6) or "no department crosses the 15% line"

    q7, q8 = read_csv("q07_paid_zero_attendance"), read_csv("q08_paid_after_separation")
    q7_amt = sum(num(r["earnings_paid"]) for r in q7)
    q8_amt = sum(num(r["earnings_paid"]) for r in q8)
    q8_emps = len({r["emp_id"] for r in q8})
    n3, h3, nz, hz = conn.execute(EVIDENCE_Q3).fetchone()
    n3, h3, nz, hz = n3 or 0, h3 or 0, nz or 0, hz or 0

    text = f"""# Top 3 findings for the CFO  (DRAFT: numbers come from the warehouse, check the wording before the demo)

## Finding 1: Paid overtime does not match the hours the punches support
Over April to September 2026 the punches show **{comp:,.0f} overtime hours**, approved requests total
**{appr:,.0f} hours** and payroll paid **{paid:,.0f} hours** (PKR {paid_amt:,.0f}). Paid overtime is
**{rel(paid, comp)}** the hours actually worked. Largest gaps: {top}.
*Evidence:* `analytics/q05_overtime_computed_vs_approved_vs_paid.sql`, `analytics/q06_paid_ot_gap.sql`.
*Recommended action:* make payroll pay overtime only up to the hours confirmed by punches, and review the
departments with the largest gap first.

## Finding 2: Money leaves payroll for people who are not at work
**{len(q7)} employee-months** were paid (PKR {q7_amt:,.0f}) with zero attendance in that month, and
**{q8_emps} separated employees** kept receiving pay after the month they left (PKR {q8_amt:,.0f} in total).
*Evidence:* `analytics/q07_paid_zero_attendance.sql`, `analytics/q08_paid_after_separation.sql`.
*Recommended action:* block payroll runs for employees past their separation month and add a monthly
"paid but no attendance" exception report for HR and Finance to sign off.

## Finding 3: Overtime approvals are not checked against real work
Of **{n3:,} approved overtime requests** ({h3:,.0f} hours), **{nz:,} requests ({hz:,.0f} hours)** fall on days
where the punches show no overtime at all.
*Evidence query:*
```sql
{EVIDENCE_Q3}
```
*Recommended action:* auto-validate every overtime approval against that day's punches before it reaches
payroll, and report approvers whose approvals are often unsupported.
"""
    OUT.write_text(text, encoding="utf-8")
    print(f"  wrote {OUT.relative_to(config.ROOT)}")
