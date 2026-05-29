def txn_delta(txn_type, amount):
    return amount if txn_type == "income" else -amount


def running_balances_by_id(rows, opening_balance=0.0):
    """Compute running balance after each transaction (chronological order)."""
    sorted_rows = sorted(rows, key=lambda r: (r["date"], r["id"]))
    balance = opening_balance
    result = {}
    for r in sorted_rows:
        balance += txn_delta(r["type"], r["amount"])
        result[r["id"]] = balance
    return result
