"""
Dashboard View.
Presents key financial and vault inventory metrics, quick shortcuts, and recent pledges table.
"""
import tkinter as tk
from tkinter import ttk
from config import THEME
from database.models import PledgeDAO, SettingsDAO
from ui.components.stat_card import StatCard

class DashboardView(tk.Frame):
    def __init__(self, parent, navigation_callback, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.navigation_callback = navigation_callback

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # Main scrollable canvas container if window is small
        self.grid_columnconfigure(0, weight=1)

        # Header Title Banner
        header = tk.Frame(self, bg=THEME["bg_main"], pady=10)
        header.pack(fill="x", padx=25, pady=(15, 10))

        settings = SettingsDAO.get_all()
        shop_title = settings.get("shop_name", "SWARNA RATNA JEWEL MORTGAGE BANKERS")

        lbl_greeting = tk.Label(
            header,
            text=f"Welcome to {shop_title}",
            font=("Segoe UI", 16, "bold"),
            bg=THEME["bg_main"],
            fg=THEME["text_dark"]
        )
        lbl_greeting.pack(anchor="w")

        lbl_sub = tk.Label(
            header,
            text="Real-time Vault Inventory, Active Mortgage Loans & Anti-Fraud Security Overview",
            font=("Segoe UI", 9),
            bg=THEME["bg_main"],
            fg=THEME["text_muted"]
        )
        lbl_sub.pack(anchor="w")

        # Metric Cards Grid (2 rows of 3 cards)
        cards_frame = tk.Frame(self, bg=THEME["bg_main"])
        cards_frame.pack(fill="x", padx=25, pady=(0, 15))

        for col in range(3):
            cards_frame.grid_columnconfigure(col, weight=1, uniform="stat_col")

        self.card_active_amt = StatCard(cards_frame, "Active Cash Disbursed", "₹ 0.00", "Total principal in vault", icon="💰", accent_color=THEME["primary"])
        self.card_active_amt.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        self.card_active_pledges = StatCard(cards_frame, "Active Pledges", "0", "Articles currently in vault", icon="📦", accent_color="#0284c7")
        self.card_active_pledges.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        self.card_gold_wt = StatCard(cards_frame, "Gold in Vault", "0.00 g", "Gold items (2% / gram)", icon="🪙", accent_color="#d97706")
        self.card_gold_wt.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")

        self.card_silver_wt = StatCard(cards_frame, "Silver in Vault", "0.00 g", "Silver items (3% / gram)", icon="🥈", accent_color="#64748b")
        self.card_silver_wt.grid(row=1, column=0, padx=6, pady=6, sticky="nsew")

        self.card_released_amt = StatCard(cards_frame, "Redeemed / Collected", "₹ 0.00", "Principal + Interest received", icon="🔓", accent_color=THEME["success"])
        self.card_released_amt.grid(row=1, column=1, padx=6, pady=6, sticky="nsew")

        self.card_customers = StatCard(cards_frame, "Total Customers", "0", "Registered customer base", icon="👥", accent_color="#8b5cf6")
        self.card_customers.grid(row=1, column=2, padx=6, pady=6, sticky="nsew")

        # Quick Actions Bar
        actions_frame = tk.Frame(self, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=16, pady=12)
        actions_frame.pack(fill="x", padx=25, pady=(0, 15))

        lbl_acts = tk.Label(actions_frame, text="QUICK ACTIONS:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_muted"])
        lbl_acts.pack(side="left", padx=(0, 15))

        btn_new = tk.Button(
            actions_frame,
            text="➕ New Mortgage Pledge",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["primary"],
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.navigation_callback("new_entry")
        )
        btn_new.pack(side="left", padx=4)

        btn_rel = tk.Button(
            actions_frame,
            text="🔓 Release Jewelry",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["success"],
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.navigation_callback("release")
        )
        btn_rel.pack(side="left", padx=4)

        btn_search = tk.Button(
            actions_frame,
            text="🔍 Search Customer / Pledges",
            font=("Segoe UI", 9, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.navigation_callback("search")
        )
        btn_search.pack(side="left", padx=4)

        btn_reg = tk.Button(
            actions_frame,
            text="📋 Day Book Register",
            font=("Segoe UI", 9, "bold"),
            bg="#475569",
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.navigation_callback("register")
        )
        btn_reg.pack(side="left", padx=4)

        # Recent Pledges Table
        recent_frame = tk.Frame(self, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=16, pady=12)
        recent_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        tbl_header = tk.Frame(recent_frame, bg=THEME["bg_card"])
        tbl_header.pack(fill="x", pady=(0, 8))

        tk.Label(
            tbl_header,
            text="Recent Mortgage Pledges",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["text_dark"]
        ).pack(side="left")

        btn_view_all = tk.Button(
            tbl_header,
            text="View All Directory →",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["primary_dark"],
            relief="flat",
            cursor="hand2",
            command=lambda: self.navigation_callback("search")
        )
        btn_view_all.pack(side="right")

        # Treeview
        columns = ("pledge_no", "date", "customer", "phone", "jewel", "type", "net_wt", "principal", "status")
        self.tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=8)

        self.tree.heading("pledge_no", text="Pledge No")
        self.tree.heading("date", text="Date")
        self.tree.heading("customer", text="Customer Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("jewel", text="Jewel Item")
        self.tree.heading("type", text="Type")
        self.tree.heading("net_wt", text="Net Wt (g)")
        self.tree.heading("principal", text="Principal (₹)")
        self.tree.heading("status", text="Status")

        self.tree.column("pledge_no", width=90, anchor="center")
        self.tree.column("date", width=90, anchor="center")
        self.tree.column("customer", width=160, anchor="w")
        self.tree.column("phone", width=110, anchor="center")
        self.tree.column("jewel", width=160, anchor="w")
        self.tree.column("type", width=70, anchor="center")
        self.tree.column("net_wt", width=80, anchor="e")
        self.tree.column("principal", width=110, anchor="e")
        self.tree.column("status", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(recent_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def refresh_data(self):
        """Fetches fresh metrics and recent entries from database."""
        stats = PledgeDAO.get_dashboard_stats()

        self.card_active_amt.update_value(f"₹ {stats.get('active_amount', 0):,.2f}")
        self.card_active_pledges.update_value(str(stats.get("active_pledges", 0)))
        self.card_gold_wt.update_value(f"{stats.get('active_gold_weight', 0):,.2f} g")
        self.card_silver_wt.update_value(f"{stats.get('active_silver_weight', 0):,.2f} g")
        self.card_released_amt.update_value(f"₹ {stats.get('released_collected', 0):,.2f}")
        self.card_customers.update_value(str(stats.get("total_customers", 0)))

        # Refresh recent pledges
        for item in self.tree.get_children():
            self.tree.delete(item)

        recent = PledgeDAO.search(limit=10)
        for r in recent:
            jtype = "Gold" if r["jewel_type"] == "G" else ("Silver" if r["jewel_type"] == "S" else "Other")
            status_text = "🟢 ACTIVE" if r["status"] == "ACTIVE" else "🔵 RELEASED"
            self.tree.insert("", "end", values=(
                r["pledge_no"],
                r["pledge_date"],
                r["customer_name"],
                r.get("customer_phone", ""),
                r["jewel_name"],
                jtype,
                f"{r['net_weight']:.2f}",
                f"₹ {r['principal_amount']:,.2f}",
                status_text
            ))
