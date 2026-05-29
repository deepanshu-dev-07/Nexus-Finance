import os
import shutil
import sqlite3
from datetime import datetime

from models import (
    DEFAULT_ACCOUNTS,
    DEFAULT_EXPENSE_CATEGORIES,
    DEFAULT_INCOME_CATEGORIES,
)
from paths import db_path as default_db_path


class Database:
    def __init__(self, path=None):
        self.path = path or default_db_path()
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def reconnect(self):
        self.close()
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row

    def backup_to(self, dest_path):
        self.conn.commit()
        shutil.copy2(self.path, dest_path)

    def restore_from(self, src_path):
        if not os.path.isfile(src_path):
            raise FileNotFoundError(f"Backup file not found: {src_path}")
        self.close()
        shutil.copy2(src_path, self.path)
        self.reconnect()
        self._init_schema()

    def get_account_opening_balance(self, name):
        row = self.conn.execute(
            "SELECT opening_balance FROM accounts WHERE name = ?", (name,)
        ).fetchone()
        return row[0] if row else 0.0

    def _init_schema(self):
        c = self.conn
        c.execute(
            """CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            date TEXT,
            type TEXT,
            category TEXT,
            account TEXT,
            amount REAL,
            description TEXT,
            currency_code TEXT DEFAULT 'INR',
            created_at TEXT
        )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            type TEXT
        )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            opening_balance REAL DEFAULT 0
        )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY,
            category TEXT,
            month TEXT,
            limit_amount REAL
        )"""
        )
        self._migrate_transactions_columns()
        self._seed_defaults()
        c.commit()

    def _migrate_transactions_columns(self):
        cols = {row[1] for row in self.conn.execute("PRAGMA table_info(transactions)")}
        if "currency_code" not in cols:
            self.conn.execute(
                "ALTER TABLE transactions ADD COLUMN currency_code TEXT DEFAULT 'INR'"
            )

    def _seed_defaults(self):
        if not self.get_setting("currency_code"):
            self.save_setting("currency_code", "INR")
        if not self.get_setting("appearance_mode"):
            self.save_setting("appearance_mode", "dark")
        cur = self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if cur == 0:
            for name in DEFAULT_EXPENSE_CATEGORIES:
                self.conn.execute(
                    "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
                    (name, "expense"),
                )
            for name in DEFAULT_INCOME_CATEGORIES:
                self.conn.execute(
                    "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
                    (name, "income"),
                )
        cur = self.conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        if cur == 0:
            for name in DEFAULT_ACCOUNTS:
                self.conn.execute(
                    "INSERT OR IGNORE INTO accounts (name, opening_balance) VALUES (?, 0)",
                    (name,),
                )

    def get_setting(self, key, default=None):
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else default

    def save_setting(self, key, value):
        self.conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    def get_categories(self, txn_type=None):
        if txn_type:
            rows = self.conn.execute(
                "SELECT name FROM categories WHERE type = ? ORDER BY name",
                (txn_type,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT name FROM categories ORDER BY name"
            ).fetchall()
        return [r[0] for r in rows]

    def add_category(self, name, txn_type):
        self.conn.execute(
            "INSERT INTO categories (name, type) VALUES (?, ?)", (name, txn_type)
        )
        self.conn.commit()

    def delete_category(self, name):
        self.conn.execute("DELETE FROM categories WHERE name = ?", (name,))
        self.conn.commit()

    def get_accounts(self):
        rows = self.conn.execute(
            "SELECT id, name, opening_balance FROM accounts ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]

    def add_account(self, name, opening_balance=0):
        self.conn.execute(
            "INSERT INTO accounts (name, opening_balance) VALUES (?, ?)",
            (name, opening_balance),
        )
        self.conn.commit()

    def update_account_balance(self, name, opening_balance):
        self.conn.execute(
            "UPDATE accounts SET opening_balance = ? WHERE name = ?",
            (opening_balance, name),
        )
        self.conn.commit()

    def delete_account(self, name):
        self.conn.execute("DELETE FROM accounts WHERE name = ?", (name,))
        self.conn.commit()

    def insert_transaction(self, data):
        currency = data.get("currency_code") or self.get_setting("currency_code", "INR")
        self.conn.execute(
            """INSERT INTO transactions
            (date, type, category, account, amount, description, currency_code, created_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            (
                data["date"],
                data["type"],
                data["category"],
                data["account"],
                data["amount"],
                data.get("description", ""),
                currency,
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()

    def update_transaction(self, txn_id, data):
        self.conn.execute(
            """UPDATE transactions SET date=?, type=?, category=?, account=?,
            amount=?, description=? WHERE id=?""",
            (
                data["date"],
                data["type"],
                data["category"],
                data["account"],
                data["amount"],
                data.get("description", ""),
                txn_id,
            ),
        )
        self.conn.commit()

    def delete_transaction(self, txn_id):
        self.conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
        self.conn.commit()

    def get_transaction(self, txn_id):
        row = self.conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (txn_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_transaction_ids(self, filters=None):
        query, params = self._build_query(
            "SELECT id FROM transactions", filters, order="date DESC, id DESC"
        )
        return [r[0] for r in self.conn.execute(query, params).fetchall()]

    def fetch_transactions(self, filters=None):
        query, params = self._build_query("SELECT * FROM transactions", filters)
        return self.conn.execute(query, params).fetchall()

    def _build_query(self, base, filters=None, order="date DESC, id DESC"):
        filters = filters or {}
        clauses = []
        params = []
        if filters.get("start_date"):
            clauses.append("date >= ?")
            params.append(filters["start_date"])
        if filters.get("end_date"):
            clauses.append("date <= ?")
            params.append(filters["end_date"])
        if filters.get("type"):
            clauses.append("type = ?")
            params.append(filters["type"])
        if filters.get("category"):
            clauses.append("category = ?")
            params.append(filters["category"])
        if filters.get("account"):
            clauses.append("account = ?")
            params.append(filters["account"])
        if filters.get("search"):
            clauses.append("(description LIKE ? OR category LIKE ?)")
            s = f"%{filters['search']}%"
            params.extend([s, s])
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        return f"{base}{where} ORDER BY {order}", params

    def account_balances(self):
        accounts = self.get_accounts()
        result = []
        for acc in accounts:
            row = self.conn.execute(
                """SELECT
                COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) AS net
                FROM transactions WHERE account = ?""",
                (acc["name"],),
            ).fetchone()
            net = row[0] if row else 0
            result.append(
                {
                    "name": acc["name"],
                    "opening": acc["opening_balance"],
                    "balance": acc["opening_balance"] + net,
                }
            )
        return result

    def get_budgets(self, month):
        rows = self.conn.execute(
            "SELECT * FROM budgets WHERE month = ?", (month,)
        ).fetchall()
        return [dict(r) for r in rows]

    def set_budget(self, category, month, limit_amount):
        existing = self.conn.execute(
            "SELECT id FROM budgets WHERE category = ? AND month = ?",
            (category, month),
        ).fetchone()
        if existing:
            self.conn.execute(
                "UPDATE budgets SET limit_amount = ? WHERE id = ?",
                (limit_amount, existing[0]),
            )
        else:
            self.conn.execute(
                "INSERT INTO budgets (category, month, limit_amount) VALUES (?,?,?)",
                (category, month, limit_amount),
            )
        self.conn.commit()

    def delete_budget(self, budget_id):
        self.conn.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        self.conn.commit()

    def category_spend(self, category, start_date, end_date):
        row = self.conn.execute(
            """SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE type='expense' AND category=? AND date>=? AND date<=?""",
            (category, start_date, end_date),
        ).fetchone()
        return row[0] if row else 0
