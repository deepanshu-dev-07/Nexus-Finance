import matplotlib.pyplot as plt
import pandas as pd


def _empty_figure(message="No data"):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.text(0.5, 0.5, message, ha="center", va="center", color="#888")
    ax.axis("off")
    fig.patch.set_facecolor("#2b2b2b")
    return fig


def expense_by_category(df):
    exp = df[df["type"] == "expense"] if not df.empty else df
    if exp.empty:
        return _empty_figure("No expenses in period")
    grouped = exp.groupby("category")["amount"].sum().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(4, 3))
    fig.patch.set_facecolor("#2b2b2b")
    ax.set_facecolor("#2b2b2b")
    grouped.plot(kind="barh", ax=ax, color="#3b8ed0")
    ax.set_title("Expenses by Category", color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#555")
    plt.tight_layout()
    return fig


def income_vs_expense_over_time(df):
    if df.empty:
        return _empty_figure("No transactions in period")
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    d["month"] = d["date"].dt.to_period("M").astype(str)
    income = d[d["type"] == "income"].groupby("month")["amount"].sum()
    expense = d[d["type"] == "expense"].groupby("month")["amount"].sum()
    months = sorted(set(income.index) | set(expense.index))
    if not months:
        return _empty_figure("No data")
    fig, ax = plt.subplots(figsize=(4, 3))
    fig.patch.set_facecolor("#2b2b2b")
    ax.set_facecolor("#2b2b2b")
    x = range(len(months))
    w = 0.35
    ax.bar([i - w / 2 for i in x], [income.get(m, 0) for m in months], w, label="Income", color="#2ecc71")
    ax.bar([i + w / 2 for i in x], [expense.get(m, 0) for m in months], w, label="Expense", color="#e74c3c")
    ax.set_xticks(list(x))
    ax.set_xticklabels(months, rotation=45, ha="right", fontsize=7, color="white")
    ax.legend(facecolor="#2b2b2b", labelcolor="white", fontsize=8)
    ax.set_title("Income vs Expense", color="white", fontsize=10)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#555")
    plt.tight_layout()
    return fig


def expense_trend(df):
    exp = df[df["type"] == "expense"].copy() if not df.empty else df
    if exp.empty:
        return _empty_figure("No expenses in period")
    exp["date"] = pd.to_datetime(exp["date"])
    daily = exp.groupby(exp["date"].dt.date)["amount"].sum()
    fig, ax = plt.subplots(figsize=(4, 3))
    fig.patch.set_facecolor("#2b2b2b")
    ax.set_facecolor("#2b2b2b")
    ax.plot(daily.index, daily.values, color="#9b59b6", linewidth=1.5)
    ax.set_title("Expense Trend", color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=7)
    for spine in ax.spines.values():
        spine.set_color("#555")
    plt.tight_layout()
    return fig


def top_categories(df, n=8):
    exp = df[df["type"] == "expense"] if not df.empty else df
    if exp.empty:
        return _empty_figure("No expenses in period")
    top = exp.groupby("category")["amount"].sum().nlargest(n)
    fig, ax = plt.subplots(figsize=(4, 3))
    fig.patch.set_facecolor("#2b2b2b")
    ax.set_facecolor("#2b2b2b")
    top.plot(kind="bar", ax=ax, color="#f39c12")
    ax.set_title(f"Top {n} Categories", color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=7, rotation=45)
    for spine in ax.spines.values():
        spine.set_color("#555")
    plt.tight_layout()
    return fig
