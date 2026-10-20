"""
Main Application Entry Point for SwarnaRatna Jewelry Mortgage & Pledge System.
"""
import sys
import os
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# Add current directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import APP_NAME, APP_SUBTITLE, APP_VERSION, THEME
from database.db import init_db
from database.models import SettingsDAO
from ui.theme import apply_theme

# Import Views
from ui.views.dashboard_view import DashboardView
from ui.views.new_entry_view import NewEntryView
from ui.views.search_view import SearchView
from ui.views.release_view import ReleaseView
from ui.views.register_view import RegisterView
from ui.views.customers_view import CustomersView
from ui.views.settings_view import SettingsView

class JewelryMortgageApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # High DPI awareness on Windows for ultra-crisp fonts and rendering
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self.title(f"{APP_NAME} - v{APP_VERSION}")
        self.geometry("1440x900")
        self.minsize(1100, 720)

        # Start maximized on Windows for optimal responsiveness & visibility
        try:
            self.state('zoomed')
        except Exception:
            pass

        # Apply Modern TTK Styles
        self.typography = apply_theme(self)

        # Navigation state
        self.nav_buttons = {}
        self.current_view_key = None

        self._build_layout()
        self.navigate_to("dashboard")

    def _build_layout(self):
        # Master Grid Layout: Column 0 = Sidebar (Width ~250px), Column 1 = Main View
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # -------------------------------------------------------------
        # LEFT SIDEBAR
        # -------------------------------------------------------------
        self.sidebar = tk.Frame(self, bg=THEME["bg_sidebar"], width=250)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Sidebar Header Branding
        brand_frame = tk.Frame(self.sidebar, bg=THEME["bg_sidebar"], padx=16, pady=20)
        brand_frame.pack(fill="x")

        lbl_logo = tk.Label(
            brand_frame,
            text="👑 SWARNA RATNA",
            font=("Segoe UI", 13, "bold"),
            bg=THEME["bg_sidebar"],
            fg=THEME["primary"]
        )
        lbl_logo.pack(anchor="w")

        lbl_sub = tk.Label(
            brand_frame,
            text="Jewel Mortgage Bankers",
            font=("Segoe UI", 8),
            bg=THEME["bg_sidebar"],
            fg="#94a3b8"
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # Divider
        div = tk.Frame(self.sidebar, bg=THEME["bg_sidebar_hover"], height=1)
        div.pack(fill="x", padx=12, pady=(0, 15))

        # Nav Buttons list: (key, label, icon)
        nav_items = [
            ("dashboard", "Dashboard", "🏠"),
            ("new_entry", "New Pledge Entry", "➕"),
            ("search", "Search & Verify", "🔍"),
            ("release", "Release Jewelry", "🔓"),
            ("register", "Day Book Register", "📋"),
            ("customers", "Customer Network", "👥"),
            ("settings", "Settings & Backup", "⚙️"),
        ]

        for key, label, icon in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=f"  {icon}  {label}",
                font=("Segoe UI", 10, "bold"),
                bg=THEME["bg_sidebar"],
                fg="#94a3b8",
                activebackground=THEME["bg_sidebar_hover"],
                activeforeground="#ffffff",
                anchor="w",
                padx=16,
                pady=11,
                relief="flat",
                borderwidth=0,
                cursor="hand2",
                command=lambda k=key: self.navigate_to(k)
            )
            btn.pack(fill="x", pady=1)
            self.nav_buttons[key] = btn

        # Sidebar Footer
        footer = tk.Frame(self.sidebar, bg=THEME["bg_sidebar"], padx=16, pady=15)
        footer.pack(side="bottom", fill="x")

        # Live clock / date
        self.lbl_clock = tk.Label(
            footer,
            text=datetime.now().strftime("%d %b %Y | %H:%M"),
            font=("Segoe UI", 8, "bold"),
            bg=THEME["bg_sidebar"],
            fg=THEME["primary"]
        )
        self.lbl_clock.pack(anchor="w")
        self._update_clock()

        lbl_status = tk.Label(
            footer,
            text="● Local SQLite (WAL Active)",
            font=("Segoe UI", 8),
            bg=THEME["bg_sidebar"],
            fg=THEME["success"]
        )
        lbl_status.pack(anchor="w", pady=(3, 0))

        lbl_ver = tk.Label(
            footer,
            text=f"Version {APP_VERSION}",
            font=("Segoe UI", 7),
            bg=THEME["bg_sidebar"],
            fg="#64748b"
        )
        lbl_ver.pack(anchor="w", pady=(2, 0))

        # -------------------------------------------------------------
        # RIGHT MAIN VIEW CONTAINER
        # -------------------------------------------------------------
        self.view_container = tk.Frame(self, bg=THEME["bg_main"])
        self.view_container.grid(row=0, column=1, sticky="nsew")
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)

    def _update_clock(self):
        now_str = datetime.now().strftime("%d %b %Y | %H:%M:%S")
        self.lbl_clock.config(text=now_str)
        self.after(1000, self._update_clock)

    def navigate_to(self, view_key, **kwargs):
        """Switches active view and updates sidebar highlight."""
        # Update sidebar button states
        for key, btn in self.nav_buttons.items():
            if key == view_key:
                btn.configure(bg=THEME["primary"], fg="#ffffff")
            else:
                btn.configure(bg=THEME["bg_sidebar"], fg="#94a3b8")

        # Clear existing view
        for child in self.view_container.winfo_children():
            child.destroy()

        self.current_view_key = view_key

        # Instantiate requested view
        if view_key == "dashboard":
            view = DashboardView(self.view_container, navigation_callback=self.navigate_to)
        elif view_key == "new_entry":
            view = NewEntryView(self.view_container, navigation_callback=self.navigate_to)
        elif view_key == "search":
            view = SearchView(self.view_container, navigation_callback=self.navigate_to)
        elif view_key == "release":
            initial_pledge = kwargs.get("pledge_no")
            view = ReleaseView(self.view_container, navigation_callback=self.navigate_to, initial_pledge_no=initial_pledge)
        elif view_key == "register":
            view = RegisterView(self.view_container, navigation_callback=self.navigate_to)
        elif view_key == "customers":
            view = CustomersView(self.view_container, navigation_callback=self.navigate_to)
        elif view_key == "settings":
            view = SettingsView(self.view_container, navigation_callback=self.navigate_to)
        else:
            view = DashboardView(self.view_container, navigation_callback=self.navigate_to)

        view.grid(row=0, column=0, sticky="nsew")

def main():
    # 1. Initialize SQLite Database & Tables
    init_db()

    # 2. Launch Tkinter GUI
    app = JewelryMortgageApp()
    app.mainloop()

if __name__ == "__main__":
    main()
