import customtkinter as ctk
import pandas as pd
from datetime import date
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt

from models import CURRENCIES
from db import Database
from dates import last_day_of_month
from views import show_dashboard, show_transactions, show_settings, show_calculators, close_calculator_charts
from views.dashboard import refresh_dashboard_body
from views.transactions import load_sheet_data

ctk.set_default_color_theme("blue")

try:
    import tksheet  # noqa: F401
except ImportError:
    pass


class FinanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nexus Finance - Money Tracker")
        self.geometry("1400x800")
        self.minsize(1280, 720)

        self.db = Database()
        mode = self.db.get_setting("appearance_mode", "dark")
        ctk.set_appearance_mode(mode)

        self.current_page = "Dashboard"
        self.txn_filters = {}
        self.txn_ids = []
        self.dashboard_period = ctk.StringVar(value="This month")
        self._chart_canvases = []
        self._calc_chart_canvases = []

        self.create_sidebar()
        self.create_main_content()
        show_dashboard(self)

    def close_dashboard_charts(self):
        for fig, canvas in self._chart_canvases:
            plt.close(fig)
            try:
                canvas.get_tk_widget().destroy()
            except Exception:
                pass
        self._chart_canvases.clear()

    def close_calculator_charts(self):
        close_calculator_charts(self)

    def after_transaction_change(self):
        if self.current_page == "Transactions" and hasattr(self, "sheet_frame"):
            load_sheet_data(self)
        elif self.current_page == "Dashboard" and hasattr(self, "dashboard_body"):
            refresh_dashboard_body(self)

    def format_money(self, value):
        code = self.db.get_setting("currency_code", "INR")
        info = CURRENCIES.get(code, CURRENCIES["INR"])
        sym = info["symbol"]
        if code == "INR":
            s = f"{value:,.2f}"
            if "." in s:
                whole, dec = s.split(".")
                whole = whole.replace(",", "")
                if len(whole) > 3:
                    last3 = whole[-3:]
                    rest = whole[:-3]
                    parts = []
                    while len(rest) > 2:
                        parts.insert(0, rest[-2:])
                        rest = rest[:-2]
                    if rest:
                        parts.insert(0, rest)
                    whole = ",".join(parts + [last3]) if parts else last3
                s = f"{whole}.{dec}"
            return f"{sym}{s}"
        return f"{sym}{value:,.2f}"

    def get_transactions_df(self, start_date=None, end_date=None, extra_filters=None):
        f = dict(extra_filters or {})
        if start_date:
            f["start_date"] = start_date
        if end_date:
            f["end_date"] = end_date
        rows = self.db.fetch_transactions(f)
        if not rows:
            return pd.DataFrame(
                columns=["id", "date", "type", "category", "account", "amount", "description"]
            )
        return pd.DataFrame([dict(r) for r in rows])

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(
            sidebar, text="Nexus Finance", font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=30)
        pages = ["Dashboard", "Transactions", "Calculators", "Budgets", "Reports", "Settings"]
        for page in pages:
            ctk.CTkButton(
                sidebar,
                text=page,
                height=45,
                command=lambda p=page: self.switch_page(p),
            ).pack(pady=6, padx=20, fill="x")

    def create_main_content(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    def switch_page(self, page):
        self.close_dashboard_charts()
        self.close_calculator_charts()
        for w in self.main_frame.winfo_children():
            w.destroy()
        handlers = {
            "Dashboard": lambda: show_dashboard(self),
            "Transactions": lambda: show_transactions(self),
            "Calculators": lambda: show_calculators(self),
            "Budgets": self.show_budgets,
            "Reports": self.show_reports,
            "Settings": lambda: show_settings(self),
        }
        handler = handlers.get(page)
        if handler:
            handler()

    # ==================== BUDGETS ====================
    def show_budgets(self):
        self.current_page = "Budgets"
        ctk.CTkLabel(self.main_frame, text="Budgets", font=ctk.CTkFont(size=28, weight="bold")).pack(
            pady=10
        )
        top = ctk.CTkFrame(self.main_frame)
        top.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(top, text="Month (YYYY-MM):").pack(side="left", padx=6)
        self.budget_month = ctk.CTkEntry(top, width=100)
        self.budget_month.insert(0, date.today().strftime("%Y-%m"))
        self.budget_month.pack(side="left", padx=4)
        ctk.CTkButton(top, text="Load", command=self._load_budgets_ui).pack(side="left", padx=8)

        add = ctk.CTkFrame(self.main_frame)
        add.pack(fill="x", padx=10, pady=4)
        self.budget_cat = ctk.CTkComboBox(add, values=self.db.get_categories("expense"), width=140)
        self.budget_cat.pack(side="left", padx=4)
        self.budget_limit = ctk.CTkEntry(add, width=120, placeholder_text="Limit amount")
        self.budget_limit.pack(side="left", padx=4)
        ctk.CTkButton(add, text="Set budget", command=self._set_budget).pack(side="left", padx=8)

        self.budget_list = ctk.CTkScrollableFrame(self.main_frame, height=500)
        self.budget_list.pack(fill="both", expand=True, padx=10, pady=10)
        self._load_budgets_ui()

    def _load_budgets_ui(self):
        for w in self.budget_list.winfo_children():
            w.destroy()
        month = self.budget_month.get().strip()
        start = f"{month}-01"
        try:
            y, m = map(int, month.split("-"))
            end = last_day_of_month(y, m).isoformat()
        except ValueError:
            messagebox.showerror("Error", "Invalid month format. Use YYYY-MM")
            return
        budgets = self.db.get_budgets(month)
        if not budgets:
            ctk.CTkLabel(self.budget_list, text="No budgets set for this month.").pack(pady=20)
            return
        for b in budgets:
            spent = self.db.category_spend(b["category"], start, end)
            limit = b["limit_amount"]
            pct = (spent / limit * 100) if limit else 0
            row = ctk.CTkFrame(self.budget_list)
            row.pack(fill="x", pady=6, padx=4)
            color = "#2ecc71" if pct < 80 else "#f39c12" if pct < 100 else "#e74c3c"
            ctk.CTkLabel(
                row,
                text=f"{b['category']}: {self.format_money(spent)} / {self.format_money(limit)} ({pct:.0f}%)",
            ).pack(side="left", padx=8)
            bar = ctk.CTkProgressBar(row, width=200)
            bar.pack(side="left", padx=8)
            bar.set(min(pct / 100, 1.0))
            bar.configure(progress_color=color)
            ctk.CTkButton(
                row, text="Delete", width=60, command=lambda bid=b["id"]: self._delete_budget(bid)
            ).pack(side="right", padx=8)

    def _set_budget(self):
        try:
            limit = float(self.budget_limit.get())
            self.db.set_budget(self.budget_cat.get(), self.budget_month.get().strip(), limit)
            self.budget_limit.delete(0, "end")
            self._load_budgets_ui()
        except ValueError:
            messagebox.showerror("Error", "Enter a valid limit amount")

    def _delete_budget(self, budget_id):
        self.db.delete_budget(budget_id)
        self._load_budgets_ui()

    # ==================== REPORTS ====================
    def show_reports(self):
        self.current_page = "Reports"
        ctk.CTkLabel(self.main_frame, text="Reports", font=ctk.CTkFont(size=28, weight="bold")).pack(
            pady=10
        )
        ctrl = ctk.CTkFrame(self.main_frame)
        ctrl.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(ctrl, text="Month (YYYY-MM):").pack(side="left", padx=6)
        self.report_month = ctk.CTkEntry(ctrl, width=100)
        self.report_month.insert(0, date.today().strftime("%Y-%m"))
        self.report_month.pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Generate", command=self._generate_report).pack(side="left", padx=8)
        ctk.CTkButton(ctrl, text="Export report CSV", command=self._export_report_csv).pack(
            side="left", padx=8
        )
        self.report_text = ctk.CTkTextbox(self.main_frame, height=520)
        self.report_text.pack(fill="both", expand=True, padx=10, pady=10)

    def _report_data(self):
        month = self.report_month.get().strip()
        start = f"{month}-01"
        y, m = map(int, month.split("-"))
        end = last_day_of_month(y, m).isoformat()
        df = self.get_transactions_df(start, end)
        return df, start, end, month

    def _generate_report(self):
        try:
            df, start, end, month = self._report_data()
        except ValueError:
            messagebox.showerror("Error", "Invalid month. Use YYYY-MM")
            return
        income = df[df["type"] == "income"]["amount"].sum() if not df.empty else 0
        expense = df[df["type"] == "expense"]["amount"].sum() if not df.empty else 0
        lines = [
            f"=== Nexus Finance Report: {month} ===",
            f"Period: {start} to {end}",
            "",
            f"Total Income:  {self.format_money(income)}",
            f"Total Expense: {self.format_money(expense)}",
            f"Net:           {self.format_money(income - expense)}",
            "",
            "--- Expense by category ---",
        ]
        if not df.empty:
            exp = df[df["type"] == "expense"]
            if not exp.empty:
                for cat, amt in exp.groupby("category")["amount"].sum().sort_values(ascending=False).items():
                    lines.append(f"  {cat}: {self.format_money(amt)}")
            lines.append("")
            lines.append("--- Largest expenses ---")
            top = exp.nlargest(10, "amount") if not exp.empty else pd.DataFrame()
            for _, r in top.iterrows():
                lines.append(
                    f"  {r['date']} {r['category']}: {self.format_money(r['amount'])} — {r['description'] or ''}"
                )
        self.report_text.delete("1.0", "end")
        self.report_text.insert("end", "\n".join(lines))

    def _export_report_csv(self):
        try:
            df, _, _, month = self._report_data()
        except ValueError:
            messagebox.showerror("Error", "Invalid month")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile=f"report_{month}.csv", filetypes=[("CSV", "*.csv")]
        )
        if not path:
            return
        df.to_csv(path, index=False)
        messagebox.showinfo("Export", "Report exported.")


if __name__ == "__main__":
    app = FinanceApp()
    app.mainloop()
