"""Task 01 | Nested Transaction Analyzer

Builds a per-customer report (successful spending, top category, rank) from a
list of transaction dictionaries.

Design decisions
* Failed (non-"success") transactions are ignored for spending, but the
  customer still appears in the report with total 0.
* A duplicate transaction id makes the whole input invalid -> ValueError.
* Ranking is "competition" style: equal spending shares the same rank
  (1, 2, 2, 4 ...).  Ordering is spending desc, then customer name asc.
"""
from __future__ import annotations

import math
from collections import defaultdict
from numbers import Real

REQUIRED_KEYS = ("id", "customer", "category", "amount", "status")
SUCCESS_STATUS = "success"


def _validate_transaction(transaction, index):
    """Raise TypeError/ValueError if a single transaction record is malformed."""
    if not isinstance(transaction, dict):
        raise TypeError(
            f"Transaction at index {index} must be a dict, "
            f"got {type(transaction).__name__}"
        )
    missing = [key for key in REQUIRED_KEYS if key not in transaction]
    if missing:
        raise ValueError(f"Transaction at index {index} is missing keys: {missing}")

    tx_id = transaction["id"]
    if isinstance(tx_id, bool) or not isinstance(tx_id, (int, str)):
        raise ValueError(f"Transaction at index {index} has an invalid id: {tx_id!r}")

    for key in ("customer", "category", "status"):
        value = transaction[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Transaction {tx_id!r}: '{key}' must be a non-empty string, got {value!r}"
            )

    amount = transaction["amount"]
    if isinstance(amount, bool) or not isinstance(amount, Real) or not math.isfinite(amount):
        raise ValueError(f"Transaction {tx_id!r}: amount must be a finite number, got {amount!r}")
    if amount < 0:
        raise ValueError(f"Transaction {tx_id!r}: amount must not be negative, got {amount!r}")


def _top_category(category_totals):
    """Category with the highest spend; ties are broken alphabetically."""
    if not category_totals:
        return None
    return min(category_totals.items(), key=lambda item: (-item[1], item[0]))[0]


def analyze_transactions(transactions):
    """Return a list of dicts: customer, total_spent, top_category, rank."""
    if not isinstance(transactions, (list, tuple)):
        raise TypeError("transactions must be a list of dictionaries")

    seen_ids = set()
    totals = {}
    category_spend = defaultdict(lambda: defaultdict(float))

    for index, transaction in enumerate(transactions):
        _validate_transaction(transaction, index)

        tx_id = transaction["id"]
        if tx_id in seen_ids:
            raise ValueError(f"Duplicate transaction id: {tx_id!r}")
        seen_ids.add(tx_id)

        customer = transaction["customer"].strip()
        totals.setdefault(customer, 0)  # customer exists even if all failed

        if transaction["status"].strip().lower() == SUCCESS_STATUS:
            amount = transaction["amount"]
            totals[customer] += amount
            category_spend[customer][transaction["category"].strip()] += amount

    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))

    report = []
    rank = 0
    previous_total = None
    for position, (customer, total) in enumerate(ordered, start=1):
        if total != previous_total:
            rank = position
            previous_total = total
        report.append(
            {
                "customer": customer,
                "total_spent": total,
                "top_category": _top_category(category_spend.get(customer)),
                "rank": rank,
            }
        )
    return report


def main():
    sample = [
        {"id": 1, "customer": "Ali", "category": "Food", "amount": 500, "status": "success"},
        {"id": 2, "customer": "Ali", "category": "Travel", "amount": 200, "status": "failed"},
        {"id": 3, "customer": "Sara", "category": "Food", "amount": 700, "status": "success"},
        {"id": 4, "customer": "Bilal", "category": "Food", "amount": 50, "status": "failed"},
    ]
    for row in analyze_transactions(sample):
        print(row)

    try:
        analyze_transactions(sample + [dict(sample[0])])
    except ValueError as error:
        print("Rejected:", error)


if __name__ == "__main__":
    main()
