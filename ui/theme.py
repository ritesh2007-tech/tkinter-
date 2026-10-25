"""
Modern TTK styling, theme definitions, colors, and typography.
Bigger fonts, responsive dimensions, and prominent visible buttons.
"""
import tkinter as tk
from tkinter import ttk, font as tkfont
from config import THEME

def apply_theme(root):
    """Configures ttk styles for a modern, clean, high-contrast, and responsive UI."""
    style = ttk.Style()
    
    # Use 'clam' or 'alt' as base for customizable ttk elements
    try:
        style.theme_use('clam')
    except Exception:
        pass

    # Global window config
    root.configure(bg=THEME["bg_main"])

    # Responsive, Bigger Fonts
    font_family = "Segoe UI" if "Segoe UI" in tkfont.families() else "Helvetica"
    font_title = (font_family, 18, "bold")
    font_subtitle = (font_family, 14, "bold")
    font_body = (font_family, 12)
    font_bold = (font_family, 12, "bold")
    font_small = (font_family, 11)
    font_large_num = (font_family, 28, "bold")
    font_btn = (font_family, 12, "bold")

    # Frame styles
    style.configure("Main.TFrame", background=THEME["bg_main"])
    style.configure("Card.TFrame", background=THEME["bg_card"], relief="solid", borderwidth=1)
    style.configure("Sidebar.TFrame", background=THEME["bg_sidebar"])

    # Label styles
    style.configure("TLabel", background=THEME["bg_main"], foreground=THEME["text_dark"], font=font_body)
    style.configure("Card.TLabel", background=THEME["bg_card"], foreground=THEME["text_dark"], font=font_body)
    style.configure("CardTitle.TLabel", background=THEME["bg_card"], foreground=THEME["text_dark"], font=font_subtitle)
    style.configure("Muted.TLabel", background=THEME["bg_main"], foreground=THEME["text_muted"], font=font_small)
    style.configure("CardMuted.TLabel", background=THEME["bg_card"], foreground=THEME["text_muted"], font=font_small)
    
    # Primary Label Headings
    style.configure("Heading.TLabel", background=THEME["bg_main"], foreground=THEME["text_dark"], font=font_title)
    style.configure("GoldHeading.TLabel", background=THEME["bg_main"], foreground=THEME["primary_dark"], font=font_title)

    # LabelFrames
    style.configure("Card.TLabelframe", background=THEME["bg_card"], bordercolor=THEME["border"], relief="solid", borderwidth=1)
    style.configure("Card.TLabelframe.Label", background=THEME["bg_card"], foreground=THEME["primary_dark"], font=font_subtitle)

    # Entry styles with comfortable height and padding
    style.configure("TEntry", fieldbackground="#ffffff", foreground=THEME["text_dark"], font=font_body, padding=8)
    style.map("TEntry",
              fieldbackground=[("focus", "#ffffff"), ("disabled", "#f1f5f9")],
              bordercolor=[("focus", THEME["primary"])])

    # Combobox styles with larger padding
    style.configure("TCombobox", fieldbackground="#ffffff", background="#ffffff", foreground=THEME["text_dark"], font=font_body, padding=8)

    # Bigger, Prominent Buttons
    # 1. Primary Button (Warm Amber Gold)
    style.configure("Primary.TButton",
                    background=THEME["primary"],
                    foreground="#ffffff",
                    font=font_btn,
                    padding=(16, 10),
                    borderwidth=0,
                    focusthickness=0)
    style.map("Primary.TButton",
              background=[("active", THEME["primary_dark"]), ("disabled", "#cbd5e1")],
              foreground=[("disabled", "#94a3b8")])

    # 2. Secondary Button
    style.configure("Secondary.TButton",
                    background="#cfd5de",
                    foreground=THEME["text_dark"],
                    font=font_btn,
                    padding=(14, 8),
                    borderwidth=0)
    style.map("Secondary.TButton",
              background=[("active", "#cbd5e1")])

    # 3. Success Button (Emerald Green)
    style.configure("Success.TButton",
                    background=THEME["success"],
                    foreground="#ffffff",
                    font=font_btn,
                    padding=(16, 10),
                    borderwidth=0)
    style.map("Success.TButton",
              background=[("active", "#15803d")])

    # 4. Danger Button (Crimson)
    style.configure("Danger.TButton",
                    background=THEME["danger"],
                    foreground="#ffffff",
                    font=font_btn,
                    padding=(14, 8),
                    borderwidth=0)
    style.map("Danger.TButton",
              background=[("active", "#b91c1c")])

    # 5. Sidebar Navigation Button (Generous click targets)
    style.configure("Nav.TButton",
                    background=THEME["bg_sidebar"],
                    foreground="#94a3b8",
                    font=font_body,
                    anchor="w",
                    padding=(18, 12),
                    borderwidth=0)
    style.map("Nav.TButton",
              background=[("active", THEME["bg_sidebar_hover"])],
              foreground=[("active", "#ffffff")])

    style.configure("NavActive.TButton",
                    background=THEME["primary"],
                    foreground="#ffffff",
                    font=font_bold,
                    anchor="w",
                    padding=(18, 12),
                    borderwidth=0)

    # Modern Treeview Styling with taller rows
    style.configure("Treeview",
                    background="#ffffff",
                    foreground=THEME["text_dark"],
                    fieldbackground="#ffffff",
                    rowheight=36,
                    font=font_body,
                    borderwidth=0)
    style.map("Treeview",
              background=[("selected", THEME["primary_light"])],
              foreground=[("selected", THEME["primary_dark"])])

    style.configure("Treeview.Heading",
                    background="#0f172a",
                    foreground="#ffffff",
                    font=font_bold,
                    padding=10,
                    borderwidth=0)
    style.map("Treeview.Heading",
              background=[("active", "#1e293b")])

    return {
        "font_family": font_family,
        "font_title": font_title,
        "font_subtitle": font_subtitle,
        "font_body": font_body,
        "font_bold": font_bold,
        "font_small": font_small,
        "font_large_num": font_large_num,
        "font_btn": font_btn
    }
