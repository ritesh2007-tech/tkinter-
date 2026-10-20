"""
Smart Autocomplete Entry with Customer Photo & Details.
Detects existing customers while typing. If selected, auto-fills form;
otherwise allows seamless automatic new entry creation.
"""
import os
import tkinter as tk
from tkinter import ttk
from config import THEME
from database.models import CustomerDAO
from services.image_service import ImageService

class CustomerAutocompleteEntry(tk.Frame):
    def __init__(self, parent, on_select_callback=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_card"], **kwargs)
        self.on_select_callback = on_select_callback
        self.popup = None
        self.search_results = []
        self._thumb_cache = []

        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, font=("Segoe UI", 10))
        self.entry.pack(fill="x", expand=True)

        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Down>", self._on_down_key)

    def get(self):
        return self.var.get()

    def set(self, text):
        self.var.set(text)

    def _on_key_release(self, event):
        if event.keysym in ("Down", "Up", "Return", "Escape"):
            return

        query = self.var.get().strip()
        if len(query) < 2:
            self._close_popup()
            return

        results = CustomerDAO.search(query, limit=6)
        if results:
            self._show_popup(results)
        else:
            self._close_popup()

    def _show_popup(self, results):
        self.search_results = results
        self._thumb_cache.clear()

        if not self.popup:
            self.popup = tk.Toplevel(self)
            self.popup.overrideredirect(True)
            self.popup.attributes("-topmost", True)
            self.popup.configure(bg="#ffffff", highlightbackground=THEME["primary"], highlightthickness=1)

        # Clear existing items
        for child in self.popup.winfo_children():
            child.destroy()

        # Update popup geometry
        self.update_idletasks()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
        w = max(420, self.entry.winfo_width())
        self.popup.geometry(f"{w}x{min(280, len(results) * 52 + 10)}+{x}+{y}")

        # Header note
        lbl_hint = tk.Label(
            self.popup,
            text="Registered Customers (Click to auto-fill or keep typing for new):",
            font=("Segoe UI", 8, "italic"),
            bg="#fef3c7",
            fg=THEME["primary_dark"],
            anchor="w",
            padx=8,
            pady=3
        )
        lbl_hint.pack(fill="x")

        # Scrollable / list container
        for idx, cust in enumerate(results):
            row_frame = tk.Frame(self.popup, bg="#ffffff", cursor="hand2", padx=6, pady=4)
            row_frame.pack(fill="x")

            # Thumbnail photo
            photo_path = cust.get("photo_path")
            thumb_path = ImageService.get_thumbnail_path(photo_path) if photo_path else None
            photo = ImageService.load_tk_image(thumb_path, size=(38, 38), placeholder_text="👤")
            self._thumb_cache.append(photo)

            lbl_img = tk.Label(row_frame, image=photo, bg="#f1f5f9", width=38, height=38)
            lbl_img.pack(side="left", padx=(0, 8))

            # Details text
            info_frame = tk.Frame(row_frame, bg="#ffffff")
            info_frame.pack(side="left", fill="x", expand=True)

            lbl_name = tk.Label(
                info_frame,
                text=cust["name"],
                font=("Segoe UI", 9, "bold"),
                bg="#ffffff",
                fg=THEME["text_dark"],
                anchor="w"
            )
            lbl_name.pack(fill="x")

            details_str = f"📞 {cust.get('phone') or 'No phone'}  |  🪪 {cust.get('aadhar') or 'No Aadhaar'}"
            lbl_sub = tk.Label(
                info_frame,
                text=details_str,
                font=("Segoe UI", 8),
                bg="#ffffff",
                fg=THEME["text_muted"],
                anchor="w"
            )
            lbl_sub.pack(fill="x")

            # Hover bindings
            def on_enter(e, f=row_frame, ifr=info_frame):
                f.configure(bg=THEME["primary_light"])
                ifr.configure(bg=THEME["primary_light"])
                for w in ifr.winfo_children():
                    w.configure(bg=THEME["primary_light"])

            def on_leave(e, f=row_frame, ifr=info_frame):
                f.configure(bg="#ffffff")
                ifr.configure(bg="#ffffff")
                for w in ifr.winfo_children():
                    w.configure(bg="#ffffff")

            def on_click(e, selected_cust=cust):
                self._select_customer(selected_cust)

            for widget in (row_frame, lbl_img, info_frame, lbl_name, lbl_sub):
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<Button-1>", on_click)

    def _select_customer(self, cust):
        self.var.set(cust["name"])
        self._close_popup()
        if self.on_select_callback:
            self.on_select_callback(cust)

    def _on_down_key(self, event):
        if self.search_results and self.popup:
            # Select first result on down key
            self._select_customer(self.search_results[0])
            return "break"

    def _on_focus_out(self, event):
        # Close popup with slight delay to allow click event
        self.after(250, self._close_popup)

    def _close_popup(self):
        if self.popup:
            self.popup.destroy()
            self.popup = None
