"""
Metric Stat Card widget for the Dashboard.
"""
import tkinter as tk
from tkinter import ttk
from config import THEME

class StatCard(tk.Frame):
    def __init__(self, parent, title, value, subtitle="", icon="💰", accent_color=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=16, pady=14, **kwargs)
        self.accent_color = accent_color or THEME["primary"]
        
        # Header row (Icon + Title)
        header_frame = tk.Frame(self, bg=THEME["bg_card"])
        header_frame.pack(fill="x", anchor="w")

        self.lbl_icon = tk.Label(header_frame, text=icon, font=("Segoe UI", 16), bg=THEME["bg_card"], fg=self.accent_color)
        self.lbl_icon.pack(side="left", padx=(0, 8))

        self.lbl_title = tk.Label(header_frame, text=title.upper(), font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"], fg=THEME["text_muted"])
        self.lbl_title.pack(side="left")

        # Value Row
        self.lbl_value = tk.Label(self, text=value, font=("Segoe UI", 18, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"])
        self.lbl_value.pack(anchor="w", pady=(8, 2))

        # Subtitle Row
        self.lbl_sub = tk.Label(self, text=subtitle, font=("Segoe UI", 8), bg=THEME["bg_card"], fg=THEME["text_muted"])
        self.lbl_sub.pack(anchor="w")

    def update_value(self, value, subtitle=None):
        self.lbl_value.config(text=value)
        if subtitle is not None:
            self.lbl_sub.config(text=subtitle)
