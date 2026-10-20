"""
Toast notification widget for modern non-blocking user feedback.
"""
import tkinter as tk
from tkinter import ttk
from config import THEME

class Toast:
    @staticmethod
    def show(parent, message, toast_type="success", duration_ms=3000):
        """Displays a sleek floating toast notification that automatically dismisses."""
        bg_colors = {
            "success": THEME["success"],
            "danger": THEME["danger"],
            "warning": THEME["warning"],
            "info": THEME["accent"]
        }
        icons = {
            "success": "✓",
            "danger": "✕",
            "warning": "⚠",
            "info": "ℹ"
        }
        bg = bg_colors.get(toast_type, THEME["primary"])
        icon = icons.get(toast_type, "ℹ")

        # Create floating top-level window without borders
        toast = tk.Toplevel(parent)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=bg)

        frame = tk.Frame(toast, bg=bg, padx=16, pady=10)
        frame.pack(fill="both", expand=True)

        lbl_icon = tk.Label(frame, text=icon, font=("Segoe UI", 12, "bold"), fg="#ffffff", bg=bg)
        lbl_icon.pack(side="left", padx=(0, 10))

        lbl_msg = tk.Label(frame, text=message, font=("Segoe UI", 10, "bold"), fg="#ffffff", bg=bg)
        lbl_msg.pack(side="left")

        # Position at top-right of parent
        try:
            parent.update_idletasks()
            x = parent.winfo_rootx() + parent.winfo_width() - 320
            y = parent.winfo_rooty() + 40
            toast.geometry(f"+{max(10, x)}+{max(10, y)}")
        except Exception:
            toast.geometry("+100+100")

        # Auto destroy after duration
        toast.after(duration_ms, toast.destroy)
