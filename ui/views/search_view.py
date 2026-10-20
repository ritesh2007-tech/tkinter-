"""
Search, Verification, Update & Deletion View.
Provides:
- Multi-criteria live search across pledge records and customers
- Status indicators (🟢 ACTIVE / 🔵 RELEASED)
- Full detail inspector with photos, ID proof, jewel info, and connection tree
- Complete update functionality (update customer, photos, jewel details, connections)
- Secure deletion functionality
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox

from config import THEME, SERIAL_LETTERS
from database.models import PledgeDAO, CustomerDAO, ConnectionDAO, SettingsDAO
from services.image_service import ImageService
from services.report_service import ReportService
from ui.components.connection_tree import ConnectionTreeWidget
from ui.components.photo_picker import PhotoPicker
from ui.components.toast import Toast

JEWELRY_ITEM_TYPES = [
    "Ring", "Earring (Jhumka / Stud)", "Gulsh / Gulshan", "Chain",
    "Necklace / Haram", "Bangle (Valayal)", "Bracelet", "Anklet (Kolusu)",
    "Pendant / Dollar", "Coin / Kasu", "Waist Belt (Oddiyanam)", "Nose Pin", "Other Jewel"
]

class SearchView(tk.Frame):
    def __init__(self, parent, navigation_callback, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.navigation_callback = navigation_callback
        self.selected_pledge = None

        self._build_ui()
        self.search_records()

    def _build_ui(self):
        # -------------------------------------------------------------
        # TOP FILTER & SEARCH BAR
        # -------------------------------------------------------------
        search_card = tk.Frame(self, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=16, pady=12)
        search_card.pack(fill="x", padx=20, pady=(15, 10))

        # Title
        tk.Label(
            search_card,
            text="🔍 SEARCH & MANAGE PLEDGES",
            font=("Segoe UI", 12, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["text_dark"]
        ).pack(anchor="w", pady=(0, 10))

        filter_row = tk.Frame(search_card, bg=THEME["bg_card"])
        filter_row.pack(fill="x")

        # Search Query
        tk.Label(filter_row, text="Search Term:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(side="left", padx=(0, 6))
        self.ent_search = ttk.Entry(filter_row, width=28, font=("Segoe UI", 10))
        self.ent_search.pack(side="left", padx=(0, 15))
        self.ent_search.bind("<Return>", lambda e: self.search_records())

        # Status Filter
        tk.Label(filter_row, text="Status:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(side="left", padx=(0, 6))
        self.cmb_status = ttk.Combobox(filter_row, values=["ALL", "ACTIVE", "RELEASED"], width=10, state="readonly")
        self.cmb_status.set("ALL")
        self.cmb_status.pack(side="left", padx=(0, 15))

        # Metal Type Filter
        tk.Label(filter_row, text="Type:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(side="left", padx=(0, 6))
        self.cmb_type = ttk.Combobox(filter_row, values=["ALL", "G", "S"], width=6, state="readonly")
        self.cmb_type.set("ALL")
        self.cmb_type.pack(side="left", padx=(0, 15))

        # Series Filter
        tk.Label(filter_row, text="Series:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(side="left", padx=(0, 6))
        self.cmb_series = ttk.Combobox(filter_row, values=["ALL"] + SERIAL_LETTERS, width=6, state="readonly")
        self.cmb_series.set("ALL")
        self.cmb_series.pack(side="left", padx=(0, 15))

        # Buttons
        btn_find = tk.Button(
            filter_row,
            text="🔍 Search",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["primary"],
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.search_records
        )
        btn_find.pack(side="left", padx=(0, 8))

        btn_reset = tk.Button(
            filter_row,
            text="Reset",
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            fg=THEME["text_dark"],
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._reset_filters
        )
        btn_reset.pack(side="left")

        # -------------------------------------------------------------
        # MAIN BODY: 2-PANE (TABLE ON LEFT, INSPECTOR ON RIGHT)
        # -------------------------------------------------------------
        paned = tk.PanedWindow(self, orient="horizontal", bg=THEME["bg_main"], sashwidth=4)
        paned.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Left: Results Table Frame
        tbl_frame = tk.Frame(paned, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1)
        paned.add(tbl_frame, width=580)

        # Treeview
        cols = ("pledge_no", "date", "customer", "phone", "jewel", "type", "net_wt", "principal", "status")
        self.tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("pledge_no", text="Pledge No")
        self.tree.heading("date", text="Date")
        self.tree.heading("customer", text="Customer Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("jewel", text="Jewel Item")
        self.tree.heading("type", text="Type")
        self.tree.heading("net_wt", text="Net Wt (g)")
        self.tree.heading("principal", text="Principal (₹)")
        self.tree.heading("status", text="Status")

        self.tree.column("pledge_no", width=85, anchor="center")
        self.tree.column("date", width=85, anchor="center")
        self.tree.column("customer", width=140, anchor="w")
        self.tree.column("phone", width=100, anchor="center")
        self.tree.column("jewel", width=130, anchor="w")
        self.tree.column("type", width=50, anchor="center")
        self.tree.column("net_wt", width=75, anchor="e")
        self.tree.column("principal", width=95, anchor="e")
        self.tree.column("status", width=90, anchor="center")

        tree_scroll = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select_record)

        # Right: Detail Inspector Frame
        self.detail_frame = tk.Frame(paned, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1)
        paned.add(self.detail_frame, width=460)

        self._build_inspector_empty()

    def _build_inspector_empty(self):
        for child in self.detail_frame.winfo_children():
            child.destroy()
        lbl = tk.Label(
            self.detail_frame,
            text="👈 Select a pledge from the table to view full photo proofs, details, and connection tree.",
            font=("Segoe UI", 10, "italic"),
            bg=THEME["bg_card"],
            fg=THEME["text_muted"],
            wraplength=380,
            justify="center"
        )
        lbl.pack(expand=True, padx=20)

    def _on_select_record(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        item_id = selected_items[0]
        values = self.tree.item(item_id, "values")
        if not values:
            return
        pledge_no = values[0]
        record = PledgeDAO.get_by_pledge_no(pledge_no)
        if record:
            self.selected_pledge = record
            self._render_inspector(record)

    def _render_inspector(self, record):
        """Renders comprehensive record detail inspector with photos and connection tree."""
        for child in self.detail_frame.winfo_children():
            child.destroy()

        # Canvas with scrollbar for inspector
        canvas = tk.Canvas(self.detail_frame, bg=THEME["bg_card"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.detail_frame, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg=THEME["bg_card"], padx=16, pady=12)

        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_win = canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_insp_resize(e):
            canvas.itemconfig(canvas_win, width=e.width)

        canvas.bind("<Configure>", _on_insp_resize)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Top Bar: Pledge No & Status Badge
        top_bar = tk.Frame(content, bg=THEME["bg_card"])
        top_bar.pack(fill="x", pady=(0, 8))

        tk.Label(top_bar, text=f"PLEDGE: {record['pledge_no']}", font=("Segoe UI", 14, "bold"), bg=THEME["bg_card"], fg=THEME["primary_dark"]).pack(side="left")

        status_color = THEME["success"] if record["status"] == "ACTIVE" else THEME["accent"]
        status_text = "🟢 ACTIVE (IN VAULT)" if record["status"] == "ACTIVE" else "🔵 RELEASED"
        tk.Label(top_bar, text=status_text, font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=status_color).pack(side="right")

        # Photos Gallery Row (Customer Photo, ID Proof, Jewel Photo)
        gallery_frame = tk.Frame(content, bg="#f8fafc", highlightbackground=THEME["border"], highlightthickness=1, padx=6, pady=6)
        gallery_frame.pack(fill="x", pady=(0, 10))

        # Customer Photo
        c_box = tk.Frame(gallery_frame, bg="#f8fafc")
        c_box.pack(side="left", padx=5)
        tk.Label(c_box, text="Customer", font=("Segoe UI", 8, "bold"), bg="#f8fafc", fg=THEME["text_muted"]).pack()
        c_thumb = ImageService.get_thumbnail_path(record.get("customer_photo_path"))
        c_img = ImageService.load_tk_image(c_thumb, size=(75, 85), placeholder_text="👤")
        lbl_ci = tk.Label(c_box, image=c_img, bg="#ffffff", highlightthickness=1, highlightbackground="#cbd5e1")
        lbl_ci.image = c_img
        lbl_ci.pack()

        # ID Proof Photo
        id_box = tk.Frame(gallery_frame, bg="#f8fafc")
        id_box.pack(side="left", padx=5)
        tk.Label(id_box, text="ID Proof", font=("Segoe UI", 8, "bold"), bg="#f8fafc", fg=THEME["text_muted"]).pack()
        id_thumb = ImageService.get_thumbnail_path(record.get("id_proof_path"))
        id_img = ImageService.load_tk_image(id_thumb, size=(75, 85), placeholder_text="🪪")
        lbl_idi = tk.Label(id_box, image=id_img, bg="#ffffff", highlightthickness=1, highlightbackground="#cbd5e1")
        lbl_idi.image = id_img
        lbl_idi.pack()

        # Jewel Photo
        j_box = tk.Frame(gallery_frame, bg="#f8fafc")
        j_box.pack(side="left", padx=5)
        tk.Label(j_box, text="Jewel Snapshot", font=("Segoe UI", 8, "bold"), bg="#f8fafc", fg=THEME["text_muted"]).pack()
        j_thumb = ImageService.get_thumbnail_path(record.get("jewel_photo_path"))
        j_img = ImageService.load_tk_image(j_thumb, size=(75, 85), placeholder_text="💍")
        lbl_ji = tk.Label(j_box, image=j_img, bg="#ffffff", highlightthickness=1, highlightbackground="#cbd5e1")
        lbl_ji.image = j_img
        lbl_ji.pack()

        # Customer Info Section
        cust_info_box = tk.LabelFrame(content, text=" Customer Information ", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], padx=10, pady=6)
        cust_info_box.pack(fill="x", pady=(0, 10))

        def add_info_row(box, label, val):
            r = tk.Frame(box, bg=THEME["bg_card"])
            r.pack(fill="x", pady=1)
            tk.Label(r, text=f"{label}:", width=14, anchor="w", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(side="left")
            tk.Label(r, text=str(val or "N/A"), anchor="w", font=("Segoe UI", 8), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(side="left", fill="x", expand=True)

        add_info_row(cust_info_box, "Full Name", record.get("customer_name"))
        add_info_row(cust_info_box, "Father/Husband", record.get("father_guardian"))
        add_info_row(cust_info_box, "Phone", record.get("phone"))
        add_info_row(cust_info_box, "Aadhaar No", record.get("aadhar"))
        add_info_row(cust_info_box, "Address", record.get("address"))

        # Jewel & Loan Details Section
        jewel_info_box = tk.LabelFrame(content, text=" Jewelry & Mortgage Terms ", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], padx=10, pady=6)
        jewel_info_box.pack(fill="x", pady=(0, 10))

        jtype = "Gold (G) [2%/g]" if record.get("jewel_type") == "G" else "Silver (S) [3%/g]"
        add_info_row(jewel_info_box, "Jewel Item", record.get("jewel_name"))
        add_info_row(jewel_info_box, "Metal Type", jtype)
        add_info_row(jewel_info_box, "Weights", f"Gross: {record.get('gross_weight')}g  |  Net: {record.get('net_weight')}g")
        add_info_row(jewel_info_box, "Quantity", f"{record.get('quantity', 1)} piece(s)")
        add_info_row(jewel_info_box, "Hallmark", record.get("hallmark"))
        add_info_row(jewel_info_box, "Remarks", record.get("remarks"))
        add_info_row(jewel_info_box, "Date Pledged", record.get("pledge_date"))
        add_info_row(jewel_info_box, "Book / Entry", f"Book {record.get('book_no')} / Entry {record.get('entry_no')}")
        add_info_row(jewel_info_box, "Principal Loan", f"₹ {record.get('principal_amount', 0):,.2f}")
        add_info_row(jewel_info_box, "Interest Rate", f"{record.get('interest_rate_pct')}% per month")

        if record.get("status") == "RELEASED":
            rel_box = tk.LabelFrame(content, text=" Release Settlement Details ", font=("Segoe UI", 9, "bold"), bg="#f0fdf4", padx=10, pady=6)
            rel_box.pack(fill="x", pady=(0, 10))
            add_info_row(rel_box, "Released Date", record.get("released_date"))
            add_info_row(rel_box, "Handed To", record.get("released_to_person"))
            add_info_row(rel_box, "Interest Paid", f"₹ {record.get('released_interest', 0):,.2f}")
            add_info_row(rel_box, "Total Received", f"₹ {record.get('released_total_paid', 0):,.2f}")

        # Verified Connection Tree
        conn_box = tk.LabelFrame(content, text=" 👥 Verified Relatives / Connections ", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], padx=10, pady=6)
        conn_box.pack(fill="x", pady=(0, 15))

        tree_view = ConnectionTreeWidget(conn_box, is_editable=False)
        tree_view.pack(fill="both", expand=True)
        conns = ConnectionDAO.get_for_customer(record["customer_id"])
        tree_view.set_connections(conns)

        # Action Buttons
        btn_action_frame = tk.Frame(content, bg=THEME["bg_card"])
        btn_action_frame.pack(fill="x", pady=(0, 10))

        btn_edit = tk.Button(
            btn_action_frame,
            text="✏️ Edit & Update All",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["primary"],
            fg="#ffffff",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=lambda: self._open_edit_dialog(record)
        )
        btn_edit.pack(side="left", padx=(0, 6))

        if record["status"] == "ACTIVE":
            btn_rel = tk.Button(
                btn_action_frame,
                text="🔓 Release Jewel",
                font=("Segoe UI", 9, "bold"),
                bg=THEME["success"],
                fg="#ffffff",
                relief="flat",
                padx=10,
                pady=6,
                cursor="hand2",
                command=lambda: self.navigation_callback("release", pledge_no=record["pledge_no"])
            )
            btn_rel.pack(side="left", padx=(0, 6))

        btn_pdf = tk.Button(
            btn_action_frame,
            text="🖨️ PDF Slip",
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            fg=THEME["text_dark"],
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=lambda: self._generate_pdf_slip(record)
        )
        btn_pdf.pack(side="left", padx=(0, 6))

        btn_del = tk.Button(
            btn_action_frame,
            text="🗑️ Delete",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["danger"],
            fg="#ffffff",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=lambda: self._delete_record(record)
        )
        btn_del.pack(side="right")

    def search_records(self):
        """Executes search with active filters and refreshes tree."""
        query_dict = {
            "text": self.ent_search.get().strip(),
            "status": self.cmb_status.get(),
            "jewel_type": self.cmb_type.get(),
            "serial_letter": self.cmb_series.get(),
        }

        for item in self.tree.get_children():
            self.tree.delete(item)

        results = PledgeDAO.search(query_dict, limit=200)
        for r in results:
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

    def _reset_filters(self):
        self.ent_search.delete(0, "end")
        self.cmb_status.set("ALL")
        self.cmb_type.set("ALL")
        self.cmb_series.set("ALL")
        self.search_records()

    def _generate_pdf_slip(self, record):
        pdf_dir = os.path.join(os.path.expanduser("~"), "Documents")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f"Pledge_{record['pledge_no']}.pdf")
        try:
            ReportService.generate_pledge_slip_pdf(record, pdf_path)
            try:
                os.startfile(pdf_path)
            except Exception:
                pass
            messagebox.showinfo("PDF Generated", f"Pledge voucher generated:\n{pdf_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {e}")

    def _delete_record(self, record):
        """Secure deletion with Admin PIN verification."""
        pin = SettingsDAO.get("admin_pin", "1234")

        # Dialog for Admin PIN
        dlg = tk.Toplevel(self)
        dlg.title("Confirm Deletion - Security PIN")
        dlg.geometry("380x180")
        dlg.configure(bg=THEME["bg_card"])
        dlg.grab_set()

        content = tk.Frame(dlg, bg=THEME["bg_card"], padx=20, pady=15)
        content.pack(fill="both", expand=True)

        tk.Label(
            content,
            text=f"Are you sure you want to delete Pledge {record['pledge_no']}?",
            font=("Segoe UI", 10, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["danger"]
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(content, text="Enter Admin Security PIN:", font=("Segoe UI", 9), bg=THEME["bg_card"]).pack(anchor="w")
        ent_pin = ttk.Entry(content, show="*", font=("Segoe UI", 11, "bold"))
        ent_pin.pack(fill="x", pady=(2, 15))
        ent_pin.focus_set()

        def do_delete():
            if ent_pin.get().strip() != pin:
                messagebox.showerror("Security Error", "Incorrect Admin PIN!", parent=dlg)
                return
            dlg.destroy()
            PledgeDAO.delete(record["id"])
            Toast.show(self.winfo_toplevel(), f"Pledge {record['pledge_no']} deleted successfully.", "success")
            self.search_records()
            self._build_inspector_empty()

        btn_box = tk.Frame(content, bg=THEME["bg_card"])
        btn_box.pack(fill="x")

        tk.Button(btn_box, text="Confirm Delete", font=("Segoe UI", 9, "bold"), bg=THEME["danger"], fg="#ffffff", relief="flat", padx=12, pady=5, command=do_delete).pack(side="left", padx=(0, 10))
        tk.Button(btn_box, text="Cancel", font=("Segoe UI", 9), bg="#e2e8f0", relief="flat", padx=10, pady=5, command=dlg.destroy).pack(side="left")

    def _open_edit_dialog(self, record):
        """
        Comprehensive Updation Modal:
        Allows modifying Customer details, photos, jewel details, weights, remarks, and connections!
        """
        dlg = tk.Toplevel(self)
        dlg.title(f"Edit & Update Pledge Record - {record['pledge_no']}")
        dlg.geometry("860x680")
        dlg.configure(bg=THEME["bg_main"])
        dlg.grab_set()

        canvas = tk.Canvas(dlg, bg=THEME["bg_main"], highlightthickness=0)
        scroll = ttk.Scrollbar(dlg, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg=THEME["bg_main"], padx=18, pady=15)

        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        edit_win_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_edit_canvas_resize(e):
            canvas.itemconfig(edit_win_id, width=e.width)

        canvas.bind("<Configure>", _on_edit_canvas_resize)
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # 1. Customer Section
        c_frame = tk.LabelFrame(content, text=" Customer Profile Updation ", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], padx=15, pady=10)
        c_frame.pack(fill="x", pady=(0, 12))

        tk.Label(c_frame, text="Customer Name *", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_cname = ttk.Entry(c_frame)
        e_cname.insert(0, record.get("customer_name") or "")
        e_cname.pack(fill="x", pady=(2, 6))

        tk.Label(c_frame, text="Father / Husband / Guardian", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_cguard = ttk.Entry(c_frame)
        e_cguard.insert(0, record.get("father_guardian") or "")
        e_cguard.pack(fill="x", pady=(2, 6))

        row_pa = tk.Frame(c_frame, bg=THEME["bg_card"])
        row_pa.pack(fill="x", pady=(0, 6))
        row_pa.grid_columnconfigure(0, weight=1)
        row_pa.grid_columnconfigure(1, weight=1)

        c_p = tk.Frame(row_pa, bg=THEME["bg_card"])
        c_p.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        tk.Label(c_p, text="Phone", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_cphone = ttk.Entry(c_p)
        e_cphone.insert(0, record.get("phone") or "")
        e_cphone.pack(fill="x", pady=(2, 0))

        c_a = tk.Frame(row_pa, bg=THEME["bg_card"])
        c_a.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        tk.Label(c_a, text="Aadhaar", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_caadhar = ttk.Entry(c_a)
        e_caadhar.insert(0, record.get("aadhar") or "")
        e_caadhar.pack(fill="x", pady=(2, 0))

        tk.Label(c_frame, text="Address", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        t_caddr = tk.Text(c_frame, height=2, font=("Segoe UI", 9))
        t_caddr.insert("1.0", record.get("address") or "")
        t_caddr.pack(fill="x", pady=(2, 8))

        # Photo pickers in edit mode
        photo_row = tk.Frame(c_frame, bg=THEME["bg_card"])
        photo_row.pack(fill="x")

        p_cust = PhotoPicker(photo_row, label="Customer Photo", category="customer", preview_size=(90, 100))
        p_cust.pack(side="left", padx=(0, 15))
        p_cust.set_existing_image(record.get("customer_photo_path"))

        p_id = PhotoPicker(photo_row, label="ID Proof Photo", category="id_proof", preview_size=(90, 100))
        p_id.pack(side="left")
        p_id.set_existing_image(record.get("id_proof_path"))

        # 2. Jewel Details Section
        j_frame = tk.LabelFrame(content, text=" Jewelry Details Updation ", font=("Segoe UI", 11, "bold"), bg=THEME["bg_card"], padx=16, pady=12)
        j_frame.pack(fill="x", pady=(0, 14))

        tk.Label(j_frame, text="Jewel Item Category (Select or Type e.g. Ring, Earring, Gulsh)", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_jcat = ttk.Combobox(j_frame, values=JEWELRY_ITEM_TYPES, font=("Segoe UI", 10))
        curr_desc = record.get("jewel_name") or ""
        matched_cat = next((cat for cat in JEWELRY_ITEM_TYPES if cat.lower() in curr_desc.lower()), "")
        e_jcat.set(matched_cat)
        e_jcat.pack(fill="x", pady=(2, 6))

        tk.Label(j_frame, text="Jewel Description / Specifics *", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_jname = ttk.Entry(j_frame)
        e_jname.insert(0, curr_desc)
        e_jname.pack(fill="x", pady=(2, 6))

        row_jw = tk.Frame(j_frame, bg=THEME["bg_card"])
        row_jw.pack(fill="x", pady=(0, 6))
        row_jw.grid_columnconfigure(0, weight=1)
        row_jw.grid_columnconfigure(1, weight=1)
        row_jw.grid_columnconfigure(2, weight=1)

        c1 = tk.Frame(row_jw, bg=THEME["bg_card"])
        c1.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        tk.Label(c1, text="Gross Wt (g)", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_gw = ttk.Entry(c1)
        e_gw.insert(0, str(record.get("gross_weight", 0)))
        e_gw.pack(fill="x", pady=(2, 0))

        c2 = tk.Frame(row_jw, bg=THEME["bg_card"])
        c2.grid(row=0, column=1, sticky="ew", padx=4)
        tk.Label(c2, text="Net Wt (g)", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_nw = ttk.Entry(c2)
        e_nw.insert(0, str(record.get("net_weight", 0)))
        e_nw.pack(fill="x", pady=(2, 0))

        c3 = tk.Frame(row_jw, bg=THEME["bg_card"])
        c3.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        tk.Label(c3, text="Quantity", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_qty = ttk.Entry(c3)
        e_qty.insert(0, str(record.get("quantity", 1)))
        e_qty.pack(fill="x", pady=(2, 0))

        # Hallmark
        tk.Label(j_frame, text="Hallmark / Purity Stamp", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(anchor="w", pady=(6, 0))
        e_hallmark = ttk.Combobox(j_frame, values=["916 BIS Hallmark", "916 KDM", "22 Karat (91.6%)", "18 Karat (75.0%)", "Silver 925", "Fine Silver", "Non-Hallmarked"])
        e_hallmark.set(record.get("hallmark") or "")
        e_hallmark.pack(fill="x", pady=(2, 6))

        # Remarks (BELOW JEWEL TYPE & HALLMARK)
        tk.Label(j_frame, text="Remarks / Item Condition", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_remarks = ttk.Entry(j_frame)
        e_remarks.insert(0, record.get("remarks") or "")
        e_remarks.pack(fill="x", pady=(2, 8))

        row_fin = tk.Frame(j_frame, bg=THEME["bg_card"])
        row_fin.pack(fill="x", pady=(0, 6))
        row_fin.grid_columnconfigure(0, weight=1)
        row_fin.grid_columnconfigure(1, weight=1)

        cf1 = tk.Frame(row_fin, bg=THEME["bg_card"])
        cf1.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        tk.Label(cf1, text="Principal (₹)", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_p = ttk.Entry(cf1)
        e_p.insert(0, str(record.get("principal_amount", 0)))
        e_p.pack(fill="x", pady=(2, 0))

        cf2 = tk.Frame(row_fin, bg=THEME["bg_card"])
        cf2.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        tk.Label(cf2, text="Interest Rate (%/mo - Any Custom Rate)", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        e_r = ttk.Entry(cf2)
        e_r.insert(0, str(record.get("interest_rate_pct", "")))
        e_r.pack(fill="x", pady=(2, 0))

        p_jewel = PhotoPicker(j_frame, label="Jewel Photo", category="jewel", preview_size=(110, 95))
        p_jewel.pack(anchor="w", pady=(6, 0))
        p_jewel.set_existing_image(record.get("jewel_photo_path"))

        # 3. Connection Tree
        conn_frame = tk.LabelFrame(content, text=" Verified Connections (Anti-Fraud Network) ", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], padx=15, pady=10)
        conn_frame.pack(fill="x", pady=(0, 15))

        tree_editor = ConnectionTreeWidget(conn_frame, is_editable=True)
        tree_editor.pack(fill="both", expand=True)
        conns = ConnectionDAO.get_for_customer(record["customer_id"])
        tree_editor.set_connections(conns)

        # Save Button
        def do_update():
            cname = e_cname.get().strip()
            if not cname:
                messagebox.showerror("Error", "Customer name cannot be empty.", parent=dlg)
                return

            try:
                new_gw = float(e_gw.get().strip())
                new_nw = float(e_nw.get().strip())
                new_p = float(e_p.get().strip())
                new_r = float(e_r.get().strip())
                new_qty = int(e_qty.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Please verify numeric weight and financial values.", parent=dlg)
                return

            # Update customer
            c_photo = p_cust.get_saved_image_path()
            id_photo = p_id.get_saved_image_path()
            CustomerDAO.update(
                record["customer_id"],
                cname,
                e_cguard.get().strip(),
                t_caddr.get("1.0", "end").strip(),
                e_cphone.get().strip(),
                e_caadhar.get().strip(),
                photo_path=c_photo if c_photo else None,
                id_proof_path=id_photo if id_photo else None
            )

            # Update pledge
            j_photo = p_jewel.get_saved_image_path()
            cat_val = e_jcat.get().strip()
            desc_val = e_jname.get().strip()
            combined_desc = f"{cat_val} - {desc_val}" if cat_val and cat_val != desc_val and not desc_val.startswith(cat_val) else (desc_val or cat_val)

            PledgeDAO.update(record["id"], {
                "pledge_date": record["pledge_date"],
                "jewel_name": combined_desc,
                "jewel_type": record["jewel_type"],
                "gross_weight": new_gw,
                "net_weight": new_nw,
                "quantity": new_qty,
                "hallmark": e_hallmark.get().strip(),
                "remarks": e_remarks.get().strip(),
                "jewel_photo_path": j_photo if j_photo else None,
                "principal_amount": new_p,
                "interest_rate_pct": new_r,
                "interest_calc_basis": record.get("interest_calc_basis", "MONTHLY")
            })

            # Update connections
            for conn in tree_editor.get_connections():
                if not conn.get("id"):
                    ConnectionDAO.add(
                        record["customer_id"],
                        conn["name"],
                        conn["relation"],
                        conn.get("phone", ""),
                        conn.get("details", ""),
                        conn.get("photo_path", "")
                    )

            dlg.destroy()
            Toast.show(self.winfo_toplevel(), "Pledge and customer updated successfully!", "success")
            self.search_records()
            updated_rec = PledgeDAO.get_by_id(record["id"])
            if updated_rec:
                self._render_inspector(updated_rec)

        btn_save_edit = tk.Button(
            content,
            text="✓ Save All Updates",
            font=("Segoe UI", 12, "bold"),
            bg=THEME["primary"],
            fg="#ffffff",
            activebackground=THEME["primary_dark"],
            activeforeground="#ffffff",
            relief="flat",
            padx=24,
            pady=12,
            cursor="hand2",
            command=do_update
        )
        btn_save_edit.pack(anchor="w", pady=(0, 25))
