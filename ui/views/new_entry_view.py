"""
New Pledge Entry View.
Features:
- Responsive canvas that dynamically stretches to window width (no clipped/half-visible buttons)
- No forced default values (all fields start clean and blank)
- Jewel Types: Earring, Ring, Gulsh / Gulshan, Chain, Necklace, Bangle, Bracelet, Anklet, etc.
- Remarks placed below jewel type & hallmark
- Flexible Interest Rate input supporting any custom/random percentage rate
- Anti-fraud Connection Tree with photos
- Prominent, clearly visible, large action buttons
"""
import os
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox

from config import THEME, SERIAL_LETTERS
from database.models import PledgeDAO, CustomerDAO, ConnectionDAO, SettingsDAO
from services.serial_service import SerialService
from services.interest_service import InterestService
from services.report_service import ReportService
from ui.components.photo_picker import PhotoPicker
from ui.components.multi_proof_picker import MultiProofPicker
from ui.components.autocomplete import CustomerAutocompleteEntry
from ui.components.connection_tree import ConnectionTreeWidget
from ui.components.toast import Toast

# Common Jewelry Item Categories
JEWELRY_ITEM_TYPES = [
    "Ring",
    "Earring (Jhumka / Stud)",
    "Gulsh / Gulshan",
    "Chain",
    "Necklace / Haram",
    "Bangle (Valayal)",
    "Bracelet",
    "Anklet (Kolusu / Leg Chain)",
    "Pendant / Dollar",
    "Coin / Kasu",
    "Waist Belt (Oddiyanam)",
    "Nose Pin (Mookuthi)",
    "Other Jewelry"
]

class NewEntryView(tk.Frame):
    def __init__(self, parent, navigation_callback, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.navigation_callback = navigation_callback

        self.selected_customer_id = None
        self.current_connections = []

        self._build_ui()

    def _build_ui(self):
        # -------------------------------------------------------------
        # RESPONSIVE SCROLLABLE CANVAS
        # -------------------------------------------------------------
        self.canvas = tk.Canvas(self, bg=THEME["bg_main"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_content = tk.Frame(self.canvas, bg=THEME["bg_main"])

        # Dynamically update scroll region when content changes
        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create window inside canvas and save its ID
        self.canvas_win_id = self.canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")

        # Responsively bind canvas configure to stretch content to 100% canvas width!
        def _on_canvas_resize(event):
            self.canvas.itemconfig(self.canvas_win_id, width=event.width)

        self.canvas.bind("<Configure>", _on_canvas_resize)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=10)
        self.scrollbar.pack(side="right", fill="y", pady=10)

        # -------------------------------------------------------------
        # 1. TOP HEADER & SERIAL / DATE BAR
        # -------------------------------------------------------------
        top_card = tk.Frame(self.scrollable_content, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=22, pady=16)
        top_card.pack(fill="x", padx=10, pady=(0, 15))

        # Title
        tk.Label(
            top_card,
            text="➕ NEW MORTGAGE PLEDGE ENTRY",
            font=("Segoe UI", 18, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["primary_dark"]
        ).pack(anchor="w")

        # Keep serial and date controls on separate rows so they remain visible on narrow windows.
        serial_bar = tk.Frame(top_card, bg=THEME["bg_card"])
        serial_bar.pack(fill="x", pady=(12, 0))
        serial_fields = tk.Frame(serial_bar, bg=THEME["bg_card"])
        serial_fields.pack(anchor="w")
        date_fields = tk.Frame(serial_bar, bg=THEME["bg_card"])
        date_fields.pack(anchor="w", pady=(8, 0))

        # Serial Series Letter
        tk.Label(serial_fields, text="Series:", font=("Segoe UI", 11, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(side="left", padx=(0, 6))
        self.cmb_letter = ttk.Combobox(serial_fields, values=SERIAL_LETTERS, width=4, font=("Segoe UI", 12, "bold"), state="readonly")
        self.cmb_letter.set("A")
        self.cmb_letter.pack(side="left")

        # Serial Number (NO DEFAULT VALUE)
        tk.Label(serial_fields, text="Serial No:", font=("Segoe UI", 11, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(side="left", padx=(14, 5))
        self.ent_serial_no = ttk.Entry(serial_fields, width=8, font=("Segoe UI", 12, "bold"))
        self.ent_serial_no.pack(side="left")
        self.ent_serial_no.bind("<KeyRelease>", lambda e: self._on_serial_no_change())

        # Generate Next Button
        self.btn_gen_serial = tk.Button(
            serial_fields,
            text="⚡ Next No",
            font=("Segoe UI", 10, "bold"),
            bg="#fef3c7",
            fg=THEME["primary_dark"],
            activebackground="#fde68a",
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
            command=self.load_next_serial
        )
        self.btn_gen_serial.pack(side="left", padx=(6, 12))

        # Book & Entry Indicator
        self.lbl_book_info = tk.Label(
            serial_fields,
            text="[Book - / Entry -]",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["primary_light"],
            fg=THEME["primary_dark"],
            padx=8,
            pady=4
        )
        self.lbl_book_info.pack(side="left", padx=(0, 15))

        # Date Section (NO DEFAULT VALUE)
        tk.Label(date_fields, text="Pledge Date:", font=("Segoe UI", 11, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(side="left", padx=(0, 6))
        self.ent_date = ttk.Entry(date_fields, width=14, font=("Segoe UI", 11))
        self.ent_date.pack(side="left")

        self.btn_sys_date = tk.Button(
            date_fields,
            text="📅 Today",
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg=THEME["text_dark"],
            activebackground="#cbd5e1",
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._set_today_date
        )
        self.btn_sys_date.pack(side="left", padx=(6, 0))

        # -------------------------------------------------------------
        # 2. MAIN 2-COLUMN SECTION: CUSTOMER (LEFT) & JEWEL (RIGHT)
        # -------------------------------------------------------------
        form_grid = tk.Frame(self.scrollable_content, bg=THEME["bg_main"])
        form_grid.pack(fill="x", padx=10, pady=(0, 15))
        form_grid.grid_columnconfigure(0, weight=1, uniform="form_cols")
        form_grid.grid_columnconfigure(1, weight=1, uniform="form_cols")
        form_grid.bind("<Configure>", self._on_form_resize)

        # --- LEFT COLUMN: CUSTOMER DETAILS ---
        cust_card = tk.LabelFrame(
            form_grid,
            text=" 👤 Customer Profile (Auto-Detect Shortcut) ",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["text_dark"],
            padx=18,
            pady=14,
            relief="solid",
            borderwidth=1
        )
        self.customer_card = cust_card
        cust_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Autocomplete customer name
        tk.Label(cust_card, text="Customer Full Name * (Type to search registered or enter new)", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.cust_autocomplete = CustomerAutocompleteEntry(cust_card, on_select_callback=self._on_customer_autofill)
        self.cust_autocomplete.pack(fill="x", pady=(3, 10))

        # Father / Husband / Guardian (NO DEFAULT)
        tk.Label(cust_card, text="Father / Husband / Guardian Name", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_cust_guardian = ttk.Entry(cust_card)
        self.ent_cust_guardian.pack(fill="x", pady=(3, 10))

        # Phone & Aadhaar in 2 columns (NO DEFAULT)
        row_pa = tk.Frame(cust_card, bg=THEME["bg_card"])
        row_pa.pack(fill="x", pady=(0, 10))
        row_pa.grid_columnconfigure(0, weight=1)
        row_pa.grid_columnconfigure(1, weight=1)

        col_p = tk.Frame(row_pa, bg=THEME["bg_card"])
        col_p.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        tk.Label(col_p, text="Contact Phone Number", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_cust_phone = ttk.Entry(col_p)
        self.ent_cust_phone.pack(fill="x", pady=(3, 0))

        col_a = tk.Frame(row_pa, bg=THEME["bg_card"])
        col_a.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        tk.Label(col_a, text="Aadhaar / ID Card No", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_cust_aadhar = ttk.Entry(col_a)
        self.ent_cust_aadhar.pack(fill="x", pady=(3, 0))

        # Address (NO DEFAULT)
        tk.Label(cust_card, text="Residential Address", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.txt_cust_address = tk.Text(cust_card, height=4, font=("Segoe UI", 11), relief="solid", borderwidth=1)
        self.txt_cust_address.pack(fill="x", pady=(3, 12))

        # Photos row: Customer Photo & ID Proof Photo
        photo_row = tk.Frame(cust_card, bg=THEME["bg_card"])
        photo_row.pack(fill="x")
        photo_row.grid_columnconfigure(0, weight=1)
        photo_row.grid_columnconfigure(1, weight=1)

        self.picker_cust_photo = PhotoPicker(photo_row, label="Customer Portrait Photo", category="customer", preview_size=(165, 180))
        self.picker_cust_photo.grid(row=0, column=0, sticky="nw", padx=(0, 12))

        self.picker_id_proof = MultiProofPicker(
            photo_row,
            label="ID Proof Photos (Aadhaar front/back, PAN, etc.)",
            card_size=(150, 165)
        )
        self.picker_id_proof.grid(row=0, column=1, sticky="nsew")
        photo_row.bind("<Configure>", self._on_photo_row_resize)

        # Status indicator if customer exists
        self.lbl_cust_status = tk.Label(cust_card, text="ℹ Status: Clean Entry", font=("Segoe UI", 9, "italic"), bg=THEME["bg_card"], fg=THEME["info"])
        self.lbl_cust_status.pack(anchor="w", pady=(10, 0))

        # --- RIGHT COLUMN: JEWELRY DETAILS & INTEREST CALCULATION ---
        jewel_card = tk.LabelFrame(
            form_grid,
            text=" 💍 Jewelry Details & Flexible Interest Calculator ",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["text_dark"],
            padx=18,
            pady=14,
            relief="solid",
            borderwidth=1
        )
        self.jewel_card = jewel_card
        jewel_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Jewel Metal Type Selector (Gold / Silver) - NO FORCED DEFAULT
        type_frame = tk.Frame(jewel_card, bg=THEME["bg_card"])
        type_frame.pack(fill="x", pady=(0, 10))

        tk.Label(type_frame, text="Jewel Metal Type: *", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(side="left", padx=(0, 14))
        self.jewel_type_var = tk.StringVar(value="")

        rb_gold = tk.Radiobutton(
            type_frame, text="🪙 Gold (G)", variable=self.jewel_type_var, value="G",
            font=("Segoe UI", 11, "bold"), bg=THEME["bg_card"], fg="#b45309", selectcolor=THEME["bg_card"],
            command=lambda: self._set_default_interest_rate("G")
        )
        rb_gold.pack(side="left", padx=(0, 18))

        rb_silver = tk.Radiobutton(
            type_frame, text="🥈 Silver (S)", variable=self.jewel_type_var, value="S",
            font=("Segoe UI", 11, "bold"), bg=THEME["bg_card"], fg="#475569", selectcolor=THEME["bg_card"],
            command=lambda: self._set_default_interest_rate("S")
        )
        rb_silver.pack(side="left")

        # Jewel Item Type / Category (Earring, Ring, Gulsh, etc.)
        tk.Label(jewel_card, text="Jewel Item Type / Category: * (Select or Type e.g. Ring, Earring, Gulsh)", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.cmb_jewel_type = ttk.Combobox(jewel_card, values=JEWELRY_ITEM_TYPES, font=("Segoe UI", 10))
        self.cmb_jewel_type.pack(fill="x", pady=(3, 10))
        self.cmb_jewel_type.bind("<<ComboboxSelected>>", self._on_jewel_cat_selected)

        # Jewel Description / Specific Name
        tk.Label(jewel_card, text="Jewel Description / Specifics * (e.g. 2 Gold Rings with Red Stones)", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_jewel_name = ttk.Entry(jewel_card)
        self.ent_jewel_name.pack(fill="x", pady=(3, 10))

        # Weights & Quantity row (Gross Wt, Net Wt, Qty) - NO DEFAULT
        row_wt = tk.Frame(jewel_card, bg=THEME["bg_card"])
        row_wt.pack(fill="x", pady=(0, 10))
        row_wt.grid_columnconfigure(0, weight=1)
        row_wt.grid_columnconfigure(1, weight=1)
        row_wt.grid_columnconfigure(2, weight=1)

        col_gw = tk.Frame(row_wt, bg=THEME["bg_card"])
        col_gw.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        tk.Label(col_gw, text="Gross Wt (g) *", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_gross_wt = ttk.Entry(col_gw)
        self.ent_gross_wt.pack(fill="x", pady=(3, 0))
        self.ent_gross_wt.bind("<KeyRelease>", lambda e: self._on_weight_input())

        col_nw = tk.Frame(row_wt, bg=THEME["bg_card"])
        col_nw.grid(row=0, column=1, sticky="ew", padx=5)
        tk.Label(col_nw, text="Net Wt (g) *", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_net_wt = ttk.Entry(col_nw)
        self.ent_net_wt.pack(fill="x", pady=(3, 0))
        self.ent_net_wt.bind("<KeyRelease>", lambda e: self._calculate_interest())

        col_qty = tk.Frame(row_wt, bg=THEME["bg_card"])
        col_qty.grid(row=0, column=2, sticky="ew", padx=(5, 0))
        tk.Label(col_qty, text="Quantity (Pcs)", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_qty = ttk.Entry(col_qty)
        self.ent_qty.pack(fill="x", pady=(3, 0))

        # Hallmark / Purity Stamp (NO DEFAULT)
        tk.Label(jewel_card, text="Hallmark / Purity Stamp", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.cmb_hallmark = ttk.Combobox(
            jewel_card,
            values=["916 BIS Hallmark", "916 KDM", "22 Karat (91.6%)", "18 Karat (75.0%)", "Silver 925", "Fine Silver", "Non-Hallmarked"],
            font=("Segoe UI", 10)
        )
        self.cmb_hallmark.pack(fill="x", pady=(3, 10))

        # Below Jewel Type & Hallmark: Dedicated Remarks Section (NO DEFAULT)
        tk.Label(jewel_card, text="Remarks / Item Condition", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        self.ent_remarks = ttk.Entry(jewel_card)
        self.ent_remarks.pack(fill="x", pady=(3, 12))

        # Financials Box: Principal Loan & Custom/Random Interest Rate
        fin_box = tk.Frame(jewel_card, bg="#fef3c7", highlightbackground="#f59e0b", highlightthickness=1, padx=14, pady=12)
        fin_box.pack(fill="x", pady=(0, 12))

        fin_grid = tk.Frame(fin_box, bg="#fef3c7")
        fin_grid.pack(fill="x")
        fin_grid.grid_columnconfigure(0, weight=1)
        fin_grid.grid_columnconfigure(1, weight=1)

        # Principal Cash Loan (NO DEFAULT)
        col_p = tk.Frame(fin_grid, bg="#fef3c7")
        col_p.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Label(col_p, text="Cash / Loan Given (₹) *", font=("Segoe UI", 10, "bold"), bg="#fef3c7", fg="#92400e").pack(anchor="w")
        self.ent_principal = ttk.Entry(col_p, font=("Segoe UI", 11, "bold"))
        self.ent_principal.pack(fill="x", pady=(3, 0))
        self.ent_principal.bind("<KeyRelease>", lambda e: self._calculate_interest())

        # Interest Rate % (NO DEFAULT - USER CAN ENTER ANY RANDOM / CUSTOM VALUE)
        col_i = tk.Frame(fin_grid, bg="#fef3c7")
        col_i.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        tk.Label(col_i, text="Interest Rate (% / Month) * (Any Custom %)", font=("Segoe UI", 10, "bold"), bg="#fef3c7", fg="#92400e").pack(anchor="w")
        self.ent_rate = ttk.Entry(col_i, font=("Segoe UI", 11, "bold"))
        self.ent_rate.pack(fill="x", pady=(3, 0))
        self.ent_rate.bind("<KeyRelease>", lambda e: self._calculate_interest())
        self._last_default_rate = self._configured_rate("G")
        self.ent_rate.insert(0, self._last_default_rate)

        # Live calculation breakdown bar
        self.lbl_interest_summary = tk.Label(
            fin_box,
            text="Enter Principal and Interest Rate % to view calculation breakdown.",
            font=("Segoe UI", 10, "bold"),
            bg="#fef3c7",
            fg="#78350f"
        )
        self.lbl_interest_summary.pack(anchor="w", pady=(10, 0))

        # Optional Jewel Photo Picker
        self.picker_jewel = PhotoPicker(jewel_card, label="Jewelry Snapshot Photo (Optional)", category="jewel", preview_size=(165, 135))
        self.picker_jewel.pack(anchor="w")

        # -------------------------------------------------------------
        # 3. ANTI-FRAUD CONNECTION TREE SECTION
        # -------------------------------------------------------------
        conn_frame = tk.Frame(self.scrollable_content, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=22, pady=16)
        conn_frame.pack(fill="x", padx=10, pady=(0, 20))

        self.conn_tree_widget = ConnectionTreeWidget(
            conn_frame,
            is_editable=True,
            on_connections_changed=lambda conns: setattr(self, 'current_connections', conns)
        )
        self.conn_tree_widget.pack(fill="both", expand=True)

        # -------------------------------------------------------------
        # 4. BIG, PROMINENT ACTION BAR (NEVER HALF-VISIBLE)
        # -------------------------------------------------------------
        action_bar = tk.Frame(self.scrollable_content, bg=THEME["bg_main"], pady=10)
        action_bar.pack(fill="x", padx=10, pady=(0, 40))
        action_bar.bind("<Configure>", self._on_action_bar_resize)

        self.btn_save_print = tk.Button(
            action_bar,
            text="💾 Save & Generate PDF Slip",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["primary"],
            fg="#ffffff",
            activebackground=THEME["primary_dark"],
            activeforeground="#ffffff",
            relief="flat",
            padx=22,
            pady=12,
            cursor="hand2",
            command=lambda: self._on_save(generate_pdf=True)
        )
        self.btn_save_print.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=3)

        self.btn_save_only = tk.Button(
            action_bar,
            text="✓ Save Only",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["success"],
            fg="#ffffff",
            activebackground="#15803d",
            activeforeground="#ffffff",
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2",
            command=lambda: self._on_save(generate_pdf=False)
        )
        self.btn_save_only.grid(row=0, column=1, sticky="ew", padx=8, pady=3)

        self.btn_reset = tk.Button(
            action_bar,
            text="🔄 Clear Form",
            font=("Segoe UI", 11, "bold"),
            bg="#e2e8f0",
            fg=THEME["text_dark"],
            activebackground="#cbd5e1",
            relief="flat",
            padx=18,
            pady=12,
            cursor="hand2",
            command=self.clear_form
        )
        self.btn_reset.grid(row=0, column=2, sticky="ew", padx=(8, 0), pady=3)
        for column in range(3):
            action_bar.grid_columnconfigure(column, weight=1)

    def _on_form_resize(self, event):
        if event.width < 1080:
            event.widget.grid_columnconfigure(1, weight=0)
            self.customer_card.grid_configure(row=0, column=0, columnspan=1, padx=0)
            self.jewel_card.grid_configure(row=1, column=0, columnspan=1, padx=0, pady=(12, 0))
        else:
            event.widget.grid_columnconfigure(1, weight=1)
            self.customer_card.grid_configure(row=0, column=0, columnspan=1, padx=(0, 8), pady=0)
            self.jewel_card.grid_configure(row=0, column=1, columnspan=1, padx=(8, 0), pady=0)

    def _on_photo_row_resize(self, event):
        if event.width < 760:
            self.picker_cust_photo.grid_configure(row=0, column=0, columnspan=2, pady=(0, 12))
            self.picker_id_proof.grid_configure(row=1, column=0, columnspan=2)
        else:
            self.picker_cust_photo.grid_configure(row=0, column=0, columnspan=1, pady=0)
            self.picker_id_proof.grid_configure(row=0, column=1, columnspan=1)

    def _on_action_bar_resize(self, event):
        if event.width < 820:
            for column in range(3):
                event.widget.grid_columnconfigure(column, weight=1 if column == 0 else 0)
            for row, button in enumerate((self.btn_save_print, self.btn_save_only, self.btn_reset)):
                button.grid_configure(row=row, column=0, padx=0, pady=4)
            self.scrollable_content.after_idle(lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        else:
            for column in range(3):
                event.widget.grid_columnconfigure(column, weight=1)
            self.btn_save_print.grid_configure(row=0, column=0, padx=(0, 8), pady=3)
            self.btn_save_only.grid_configure(row=0, column=1, padx=8, pady=3)
            self.btn_reset.grid_configure(row=0, column=2, padx=(8, 0), pady=3)

    def _configured_rate(self, metal_type):
        setting_key = "silver_rate_pct" if metal_type == "S" else "gold_rate_pct"
        default_rate = InterestService.get_default_rate(metal_type)
        return SettingsDAO.get(setting_key, str(default_rate)) or str(default_rate)

    def _set_default_interest_rate(self, metal_type, force=False):
        current_rate = self.ent_rate.get().strip()
        try:
            is_previous_default = not current_rate or float(current_rate) == float(self._last_default_rate)
        except ValueError:
            is_previous_default = False

        new_rate = self._configured_rate(metal_type)
        if force or is_previous_default:
            self.ent_rate.delete(0, "end")
            self.ent_rate.insert(0, new_rate)
            self._calculate_interest()
        self._last_default_rate = new_rate

    # -------------------------------------------------------------
    # HELPER LOGIC & EVENT HANDLERS
    # -------------------------------------------------------------
    def _on_jewel_cat_selected(self, event):
        cat = self.cmb_jewel_type.get().strip()
        curr_desc = self.ent_jewel_name.get().strip()
        if cat and not curr_desc:
            self.ent_jewel_name.insert(0, cat)

    def load_next_serial(self):
        letter = self.cmb_letter.get().strip().upper() or "A"
        info = SerialService.get_current_or_next_serial(letter)
        self.ent_serial_no.delete(0, "end")
        self.ent_serial_no.insert(0, str(info["serial_no"]))
        self.lbl_book_info.config(text=f"[Book {info['book_no']} / Entry {info['entry_no']}]")

    def _on_serial_no_change(self):
        val = self.ent_serial_no.get().strip()
        if val.isdigit():
            s_no = int(val)
            b_no, e_no = SerialService.calculate_book_and_entry(s_no)
            self.lbl_book_info.config(text=f"[Book {b_no} / Entry {e_no}]")
        else:
            self.lbl_book_info.config(text="[Book - / Entry -]")

    def _set_today_date(self):
        self.ent_date.delete(0, "end")
        self.ent_date.insert(0, date.today().strftime("%Y-%m-%d"))

    def _on_weight_input(self):
        # Convenience auto-fill net weight if empty
        gw = self.ent_gross_wt.get().strip()
        nw = self.ent_net_wt.get().strip()
        if gw and not nw:
            self.ent_net_wt.insert(0, gw)
            self._calculate_interest()

    def _calculate_interest(self):
        p_str = self.ent_principal.get().strip()
        r_str = self.ent_rate.get().strip()
        w_str = self.ent_net_wt.get().strip()

        if not p_str or not r_str:
            self.lbl_interest_summary.config(text="Enter Principal and Interest Rate % to view calculation breakdown.")
            return

        try:
            p = float(p_str)
            r = float(r_str)
            w = float(w_str) if w_str else 0.0
            calc = InterestService.calculate_monthly_interest(p, r, w, self.jewel_type_var.get())
            monthly_amt = calc["monthly_interest"]
            ann_pct = calc["annual_rate_pct"]
            per_g = calc["per_gram_monthly"]

            text = f"Monthly Interest: ₹ {monthly_amt:,.2f} / month  |  Annual: {ann_pct}% p.a."
            if w > 0:
                text += f"  |  ₹ {per_g:.2f}/gram"
            self.lbl_interest_summary.config(text=text)
        except Exception:
            self.lbl_interest_summary.config(text="Enter valid numeric Principal and Interest Rate %.")

    def _on_customer_autofill(self, cust):
        """Auto-populates customer data from existing database record."""
        self.selected_customer_id = cust["id"]
        self.ent_cust_guardian.delete(0, "end")
        self.ent_cust_guardian.insert(0, cust.get("father_guardian") or "")

        self.ent_cust_phone.delete(0, "end")
        self.ent_cust_phone.insert(0, cust.get("phone") or "")

        self.ent_cust_aadhar.delete(0, "end")
        self.ent_cust_aadhar.insert(0, cust.get("aadhar") or "")

        self.txt_cust_address.delete("1.0", "end")
        self.txt_cust_address.insert("1.0", cust.get("address") or "")

        # Set photos
        self.picker_cust_photo.set_existing_image(cust.get("photo_path"))
        self.picker_id_proof.set_proof_paths(CustomerDAO.get_proof_photos(cust))

        # Load existing connections for this customer
        existing_conns = ConnectionDAO.get_for_customer(cust["id"])
        self.current_connections = existing_conns
        self.conn_tree_widget.set_connections(existing_conns)

        self.lbl_cust_status.config(
            text=f"✓ Auto-Detected Customer: {cust['name']} (ID: {cust['id']})",
            fg=THEME["success"]
        )
        Toast.show(self.winfo_toplevel(), f"Auto-filled details for {cust['name']}", "info")

    def _on_save(self, generate_pdf=False):
        # 1. Validation
        cust_name = self.cust_autocomplete.get().strip()
        if not cust_name:
            messagebox.showerror("Validation Error", "Customer Name is required.")
            return

        serial_letter = self.cmb_letter.get().strip().upper()
        serial_no_str = self.ent_serial_no.get().strip()
        if not serial_no_str:
            messagebox.showerror("Validation Error", "Serial Number is required. You can click '⚡ Next No' to generate.")
            return

        is_valid, msg = SerialService.validate_serial(serial_letter, serial_no_str)
        if not is_valid:
            messagebox.showerror("Serial Error", msg)
            return

        serial_no = int(serial_no_str)
        pledge_date = self.ent_date.get().strip()
        if not pledge_date:
            messagebox.showerror("Date Error", "Please enter a Pledge Date (YYYY-MM-DD) or click '📅 Today'.")
            return

        try:
            datetime.strptime(pledge_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Date Error", "Date must be in format YYYY-MM-DD (e.g. 2026-10-17).")
            return

        jewel_cat = self.cmb_jewel_type.get().strip()
        jewel_name = self.ent_jewel_name.get().strip()
        if not jewel_name and jewel_cat:
            jewel_name = jewel_cat
        if not jewel_name:
            messagebox.showerror("Validation Error", "Jewel description or type is required.")
            return

        try:
            gross_wt = float(self.ent_gross_wt.get().strip())
            net_wt = float(self.ent_net_wt.get().strip())
            if net_wt <= 0 or gross_wt <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter valid Gross and Net weights in grams.")
            return

        try:
            principal = float(self.ent_principal.get().strip())
            if principal <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid Cash / Loan Principal Amount.")
            return

        try:
            rate_pct = float(self.ent_rate.get().strip())
            if rate_pct < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid Interest Rate % (e.g. 2.0, 1.75, 3.5).")
            return

        qty_str = self.ent_qty.get().strip()
        quantity = int(qty_str) if qty_str.isdigit() else 1

        metal_type = self.jewel_type_var.get() or "G"

        # 2. Persist Customer
        cust_photo_path = self.picker_cust_photo.get_saved_image_path()
        id_proof_path = CustomerDAO.encode_proof_photos(self.picker_id_proof.get_proof_paths())
        guardian = self.ent_cust_guardian.get().strip()
        phone = self.ent_cust_phone.get().strip()
        aadhar = self.ent_cust_aadhar.get().strip()
        address = self.txt_cust_address.get("1.0", "end").strip()

        if self.selected_customer_id:
            # Update existing customer
            CustomerDAO.update(
                self.selected_customer_id,
                cust_name, guardian, address, phone, aadhar,
                photo_path=cust_photo_path if cust_photo_path else None,
                id_proof_path=id_proof_path
            )
            cust_id = self.selected_customer_id
        else:
            # Create new customer
            cust_id = CustomerDAO.create(
                cust_name, guardian, address, phone, aadhar,
                cust_photo_path, id_proof_path
            )

        # 3. Save Connections
        connections = self.conn_tree_widget.get_connections()
        for conn in connections:
            if not conn.get("id"):
                ConnectionDAO.add(
                    cust_id,
                    conn["name"],
                    conn["relation"],
                    conn.get("phone", ""),
                    conn.get("details", ""),
                    conn.get("photo_path", "")
                )

        # 4. Save Pledge Record
        jewel_photo = self.picker_jewel.get_saved_image_path()
        combined_jewel_desc = f"{jewel_cat} - {jewel_name}" if jewel_cat and jewel_cat != jewel_name and not jewel_name.startswith(jewel_cat) else jewel_name

        pledge_payload = {
            "customer_id": cust_id,
            "serial_letter": serial_letter,
            "serial_no": serial_no,
            "pledge_date": pledge_date,
            "jewel_name": combined_jewel_desc,
            "jewel_type": metal_type,
            "gross_weight": gross_wt,
            "net_weight": net_wt,
            "quantity": quantity,
            "hallmark": self.cmb_hallmark.get().strip(),
            "remarks": self.ent_remarks.get().strip(),
            "jewel_photo_path": jewel_photo,
            "principal_amount": principal,
            "interest_rate_pct": rate_pct,
            "interest_calc_basis": "MONTHLY"
        }

        pledge_id, pledge_no = PledgeDAO.create(pledge_payload)
        Toast.show(self.winfo_toplevel(), f"Pledge {pledge_no} created successfully!", "success")

        # 5. PDF generation if requested
        if generate_pdf:
            full_pledge_data = PledgeDAO.get_by_id(pledge_id)
            pdf_dir = os.path.join(os.path.expanduser("~"), "Documents")
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f"Pledge_Ticket_{pledge_no}.pdf")
            try:
                ReportService.generate_pledge_slip_pdf(full_pledge_data, pdf_path)
                try:
                    os.startfile(pdf_path)
                except Exception:
                    pass
                messagebox.showinfo("PDF Generated", f"Pledge slip created successfully:\n{pdf_path}")
            except Exception as e:
                messagebox.showwarning("PDF Error", f"Pledge was saved, but PDF slip generation failed: {e}")

        # Reset form for next entry (ALL BLANK)
        self.clear_form()

    def clear_form(self):
        """Resets all form fields to completely blank - NO DEFAULT VALUES!"""
        self.selected_customer_id = None
        self.current_connections = []
        self.cust_autocomplete.set("")
        self.ent_cust_guardian.delete(0, "end")
        self.ent_cust_phone.delete(0, "end")
        self.ent_cust_aadhar.delete(0, "end")
        self.txt_cust_address.delete("1.0", "end")
        self.picker_cust_photo.clear_image()
        self.picker_id_proof.clear_image()
        self.lbl_cust_status.config(text="ℹ Status: Clean Entry", fg=THEME["info"])

        self.cmb_jewel_type.set("")
        self.ent_jewel_name.delete(0, "end")
        self.jewel_type_var.set("")
        self.ent_gross_wt.delete(0, "end")
        self.ent_net_wt.delete(0, "end")
        self.ent_qty.delete(0, "end")
        self.cmb_hallmark.set("")
        self.ent_remarks.delete(0, "end")
        self.ent_principal.delete(0, "end")
        self._last_default_rate = self._configured_rate("G")
        self.ent_rate.delete(0, "end")
        self.ent_rate.insert(0, self._last_default_rate)
        self.picker_jewel.clear_image()
        self.lbl_interest_summary.config(text="Enter Principal and Interest Rate % to view calculation breakdown.")

        self.ent_serial_no.delete(0, "end")
        self.lbl_book_info.config(text="[Book - / Entry -]")
        self.ent_date.delete(0, "end")

        self.conn_tree_widget.set_connections([])
