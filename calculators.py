import math

from models import DEPOSITS_PER_YEAR


def rate_to_annual(nominal_decimal, rate_period):
    """Convert entered rate (as decimal) to annual nominal rate."""
    multipliers = {
        "daily": 365,
        "weekly": 52,
        "monthly": 12,
        "quarterly": 4,
        "annual": 1,
    }
    return nominal_decimal * multipliers.get(rate_period, 1)


def effective_annual_rate(annual_nominal, compounds_per_year):
    n = max(compounds_per_year, 1)
    return (1 + annual_nominal / n) ** n - 1


def years_to_double(annual_nominal, compounds_per_year):
    apy = effective_annual_rate(annual_nominal, compounds_per_year)
    if apy <= 0:
        return None
    years = math.log(2) / math.log(1 + apy)
    whole_years = int(years)
    months = int(round((years - whole_years) * 12))
    return whole_years, months


def _build_yearly_breakdown(monthly_rows, principal):
    rows = [
        {
            "year": 0,
            "interest": None,
            "accrued_interest": None,
            "balance": principal,
        }
    ]
    prev_accrued = 0.0
    num_years = max(1, (len(monthly_rows) + 11) // 12)
    for yr in range(1, num_years + 1):
        idx = min(yr * 12 - 1, len(monthly_rows) - 1)
        if idx < 0:
            break
        m = monthly_rows[idx]
        year_interest = m["accrued_interest"] - prev_accrued
        prev_accrued = m["accrued_interest"]
        rows.append(
            {
                "year": yr,
                "interest": year_interest,
                "accrued_interest": m["accrued_interest"],
                "balance": m["balance"],
            }
        )
    return rows


def _simulate_three_way_growth(
    principal,
    annual_rate,
    total_months,
    compounds_per_year,
    deposit,
    deposit_interval,
    deposit_at_start,
    include_deposits,
):
    """
    Run compound, simple-interest, and no-interest paths in parallel each month.
    Returns chart series plus monthly row dicts for compound and simple balances.
    """
    compounds_per_month = max(1, int(round(compounds_per_year / 12)))
    rate_per_compound = annual_rate / max(compounds_per_year, 1)

    compound_bal = principal
    simple_accrued = 0.0
    cumulative_deposits = 0.0
    compound_accrued = 0.0

    labels = []
    compound_series = []
    simple_series = []
    no_interest_series = []
    compound_rows = []
    simple_rows = []

    for month in range(1, total_months + 1):
        month_deposit = 0.0
        if include_deposits and deposit > 0 and (month - 1) % deposit_interval == 0:
            month_deposit = deposit
            if deposit_at_start:
                compound_bal += month_deposit
                cumulative_deposits += month_deposit

        period_interest = 0.0
        for _ in range(compounds_per_month):
            interest = compound_bal * rate_per_compound
            compound_bal += interest
            period_interest += interest

        if include_deposits and month_deposit > 0 and not deposit_at_start:
            compound_bal += month_deposit
            cumulative_deposits += month_deposit

        compound_accrued += period_interest
        simple_accrued += principal * annual_rate / 12
        simple_bal = principal + cumulative_deposits + simple_accrued
        no_growth_bal = principal + cumulative_deposits
        total_contributed = principal + cumulative_deposits

        labels.append(str(month))
        compound_series.append(compound_bal)
        simple_series.append(simple_bal)
        no_interest_series.append(no_growth_bal)

        compound_rows.append(
            {
                "month": month,
                "deposit": month_deposit,
                "interest": period_interest,
                "accrued_interest": compound_accrued,
                "total_deposits": total_contributed,
                "balance": compound_bal,
            }
        )
        simple_rows.append(
            {
                "month": month,
                "deposit": month_deposit,
                "interest": principal * annual_rate / 12,
                "accrued_interest": simple_accrued,
                "total_deposits": total_contributed,
                "balance": simple_bal,
            }
        )

    return {
        "labels": labels,
        "compound": compound_series,
        "simple": simple_series,
        "no_interest": no_interest_series,
        "compound_rows": compound_rows,
        "simple_rows": simple_rows,
        "cumulative_deposits": cumulative_deposits,
        "compound_final": compound_bal,
        "simple_final": simple_bal,
        "simple_accrued": simple_accrued,
        "compound_accrued": compound_accrued,
    }


def _projection_summary(sim, principal, rate_percent, annual_rate, compounds_per_year, years, months, primary):
    if primary == "simple":
        final = sim["simple_final"]
        total_interest = sim["simple_accrued"]
        apy = annual_rate
        ror = ((final - principal) / principal * 100) if principal > 0 else 0
        calc_type = "simple"
    else:
        final = sim["compound_final"]
        total_interest = final - principal - sim["cumulative_deposits"]
        apy = effective_annual_rate(annual_rate, compounds_per_year)
        ror = ((final - principal) / principal * 100) if principal > 0 else 0
        calc_type = "compound"

    double_time = years_to_double(annual_rate, compounds_per_year)
    return {
        "final_value": final,
        "total_interest": total_interest,
        "initial_balance": principal,
        "total_deposits": sim["cumulative_deposits"],
        "nominal_rate_pct": rate_percent,
        "annual_nominal_pct": annual_rate * 100,
        "effective_rate_pct": apy * 100,
        "ror_pct": ror,
        "years": years,
        "months": months,
        "compounds_per_year": compounds_per_year,
        "double_years": double_time[0] if double_time else None,
        "double_months": double_time[1] if double_time else None,
        "pie_initial": principal,
        "pie_deposits": sim["cumulative_deposits"],
        "pie_interest": max(total_interest, 0),
        "calc_type": calc_type,
    }


def simple_interest_projection(
    principal,
    rate_percent,
    rate_period="annual",
    years=0,
    months=0,
    deposit=0.0,
    deposit_frequency="monthly",
    deposit_at_start=True,
    include_deposits=False,
):
    """Table/summary use simple interest; charts always show all three comparison lines."""
    annual_rate = rate_to_annual(rate_percent / 100.0, rate_period)
    total_months = max(1, int(years * 12 + months))
    dep_per_year = DEPOSITS_PER_YEAR.get(deposit_frequency, 12)
    deposit_interval = max(1, int(round(12 / dep_per_year)))

    sim = _simulate_three_way_growth(
        principal,
        annual_rate,
        total_months,
        1,
        deposit,
        deposit_interval,
        deposit_at_start,
        include_deposits,
    )
    monthly_rows = sim["simple_rows"]
    yearly_rows = _build_yearly_breakdown(monthly_rows, principal)
    summary = _projection_summary(
        sim, principal, rate_percent, annual_rate, 1, years, months, "simple"
    )
    chart_data = {
        "labels": sim["labels"],
        "compound": sim["compound"],
        "simple": sim["simple"],
        "no_interest": sim["no_interest"],
    }
    return summary, monthly_rows, yearly_rows, chart_data


def lump_sum_compound(principal, annual_rate, years):
    amount = principal * (1 + annual_rate) ** years
    return amount, amount - principal


def compound_interest_projection(
    principal,
    rate_percent,
    rate_period="annual",
    years=0,
    months=0,
    compounds_per_year=12,
    deposit=0.0,
    deposit_frequency="monthly",
    deposit_at_start=True,
    include_deposits=False,
):
    """
    Month-by-month projection matching common compound calculators.
    Returns summary dict, monthly rows, yearly rows, and chart series.
    """
    annual_rate = rate_to_annual(rate_percent / 100.0, rate_period)
    total_months = max(1, int(years * 12 + months))
    dep_per_year = DEPOSITS_PER_YEAR.get(deposit_frequency, 12)
    deposit_interval = max(1, int(round(12 / dep_per_year)))

    sim = _simulate_three_way_growth(
        principal,
        annual_rate,
        total_months,
        compounds_per_year,
        deposit,
        deposit_interval,
        deposit_at_start,
        include_deposits,
    )
    monthly_rows = sim["compound_rows"]
    yearly_rows = _build_yearly_breakdown(monthly_rows, principal)
    summary = _projection_summary(
        sim, principal, rate_percent, annual_rate, compounds_per_year, years, months, "compound"
    )
    chart_data = {
        "labels": sim["labels"],
        "compound": sim["compound"],
        "simple": sim["simple"],
        "no_interest": sim["no_interest"],
    }
    return summary, monthly_rows, yearly_rows, chart_data


def sip_future_value(monthly_payment, annual_rate, years, payment_at_start=True):
    months = int(years * 12)
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        fv = monthly_payment * months
    else:
        fv = monthly_payment * (((1 + monthly_rate) ** months - 1) / monthly_rate)
        if payment_at_start:
            fv *= 1 + monthly_rate
    invested = monthly_payment * months
    return fv, fv - invested


def sip_growth_series(monthly_payment, annual_rate, years, payment_at_start=True):
    months = int(max(years, 0.1) * 12)
    monthly_rate = annual_rate / 12
    labels, balances, invested_series = [], [], []
    balance = 0.0
    invested = 0.0
    for m in range(1, months + 1):
        if payment_at_start:
            balance += monthly_payment
            invested += monthly_payment
        if monthly_rate == 0:
            pass
        else:
            balance *= 1 + monthly_rate
        if not payment_at_start:
            balance += monthly_payment
            invested += monthly_payment
        labels.append(str(m))
        balances.append(balance)
        invested_series.append(invested)
    return labels, balances, invested_series


def emi(principal, annual_rate, tenure_months):
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        payment = principal / tenure_months
    else:
        payment = (
            principal
            * monthly_rate
            * (1 + monthly_rate) ** tenure_months
            / ((1 + monthly_rate) ** tenure_months - 1)
        )
    total = payment * tenure_months
    return payment, total, total - principal


def full_amortization_schedule(principal, annual_rate, tenure_months):
    payment, _, _ = emi(principal, annual_rate, tenure_months)
    monthly_rate = annual_rate / 12
    balance = principal
    rows = []
    labels, balance_series, principal_paid_series, interest_series = [], [], [], []
    total_principal = 0.0
    total_interest = 0.0
    for month in range(1, tenure_months + 1):
        interest = balance * monthly_rate
        principal_paid = payment - interest
        balance = max(balance - principal_paid, 0)
        total_principal += principal_paid
        total_interest += interest
        rows.append((month, payment, principal_paid, interest, balance))
        labels.append(str(month))
        balance_series.append(balance)
        principal_paid_series.append(total_principal)
        interest_series.append(total_interest)
    return rows, labels, balance_series, total_principal, total_interest


def amortization_schedule(principal, annual_rate, tenure_months, max_rows=12):
    payment, _, _ = emi(principal, annual_rate, tenure_months)
    monthly_rate = annual_rate / 12
    balance = principal
    lines = []
    for month in range(1, min(tenure_months, max_rows) + 1):
        interest = balance * monthly_rate
        principal_paid = payment - interest
        balance -= principal_paid
        lines.append((month, payment, principal_paid, interest, max(balance, 0)))
    if tenure_months > max_rows:
        lines.append(("...", None, None, None, None))
    return lines


def fd_interest(principal, annual_rate, months, compound=True):
    years = months / 12
    if compound:
        amount = principal * (1 + annual_rate / 12) ** months
    else:
        amount = principal * (1 + annual_rate * years)
    return amount, amount - principal


def fd_growth_series(principal, annual_rate, months):
    labels, compound_series, simple_series = [], [], []
    for m in range(0, months + 1):
        comp, _ = fd_interest(principal, annual_rate, m, compound=True)
        simp, _ = fd_interest(principal, annual_rate, m, compound=False)
        labels.append(str(m))
        compound_series.append(comp)
        simple_series.append(simp)
    return labels, compound_series, simple_series


def goal_monthly_sip(target, annual_rate, years):
    months = int(years * 12)
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return target / months if months else 0
    return target * monthly_rate / ((1 + monthly_rate) ** months - 1)


def goal_growth_series(monthly, annual_rate, years):
    return sip_growth_series(monthly, annual_rate, years, payment_at_start=True)


def inflation_adjusted_return(nominal_rate, inflation_rate):
    return (1 + nominal_rate) / (1 + inflation_rate) - 1
