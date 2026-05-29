CURRENCIES = {
    "INR": {"symbol": "₹", "locale": "in_IN"},
    "USD": {"symbol": "$", "locale": "en_US"},
    "EUR": {"symbol": "€", "locale": "de_DE"},
    "GBP": {"symbol": "£", "locale": "en_GB"},
}

DEFAULT_EXPENSE_CATEGORIES = ["Food", "Transport", "Rent", "Utilities", "Shopping", "Health", "Entertainment", "Other"]
DEFAULT_INCOME_CATEGORIES = ["Salary", "Freelance", "Investment", "Gift", "Other"]
DEFAULT_ACCOUNTS = ["Cash", "Bank", "Card"]

COMPOUND_FREQUENCIES = {
    "Daily (365/yr)": 365,
    "Daily (360/yr)": 360,
    "Weekly (52/yr)": 52,
    "Bi-Weekly (26/yr)": 26,
    "Monthly (12/yr)": 12,
    "Quarterly (4/yr)": 4,
    "Half-Yearly (2/yr)": 2,
    "Yearly (1/yr)": 1,
}

RATE_PERIODS = ["annual", "monthly", "quarterly", "weekly", "daily"]

DEPOSIT_FREQUENCIES = ["weekly", "bi-weekly", "monthly", "quarterly", "half-yearly", "yearly"]

DEPOSITS_PER_YEAR = {
    "weekly": 52,
    "bi-weekly": 26,
    "monthly": 12,
    "quarterly": 4,
    "half-yearly": 2,
    "yearly": 1,
}

PERIOD_OPTIONS = [
    "This month",
    "Last month",
    "Last 3 months",
    "This year",
    "All time",
    "Custom range",
]
