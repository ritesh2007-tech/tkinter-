"""
Release Jewelry / Redemption View.
Allows fast lookup by Pledge No or Customer Name.
Displays the customer profile, jewelry details, photos, and verified connection tree.
Calculates days elapsed, accrued interest, discount, and total settlement amount.
Confirms release and generates a professional PDF Release Receipt.
"""
import os
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox

from config import THEME
from database.models import PledgeDAO, ConnectionDAO
from services.interest_service import InterestService
from services.image_service import ImageService
from services.report_service import ReportService
from ui.components.connection_tree import ConnectionTreeWidget
from ui.components.toast import Toast

class ReleaseView(tk.Frame):
    def __init__(self, parent, navigation_callback, initial_pledge_no=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.navigation_callback = navigation_callback
        self.current_pledge = None
        self.initial_pledge_no = initial_pledge_no

        self._build_ui()
        if initial_pledge_no:
            self.ent_search.insert(0, initial_pledge_no)
            self.lookup_pledge()

    def _build_ui(self):
        # -------------------------------------------------------------
        # TOP LOOKUP BAR
        # -------------------------------------------------------------
        search_card = tk.Frame(self, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=20, pady=14)
        search_card.pack(fill="x", padx=25, pady=(15, 12))

        tk.Label(
            search_card,
            text="🔓 RELEASE JEWELRY / REDEMPTION DESK",
            font=("Segoe UI", 13, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["success"]
        ).pack(anchor="w", pady=(0, 10))

        bar = tk.Frame(search_card, bg=THEME["bg_card"])
        bar.pack(fill="x")

        tk.Label(bar, text="Pledge No (e.g. A-0001) or Customer Name:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(side="left", padx=(0, 10))
        self.ent_search = ttk.Entry(bar, width=28, font=("Segoe UI", 11, "bold"))
        self.ent_search.pack(side="left", padx=(0, 10))
        self.ent_search.bind("<Return>", lambda e: self.lookup_pledge())

        btn_find = tk.Button(
            bar,
            text="🔍 Find Pledge",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["primary"],
            fg="#ffffff",
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2",
            command=self.lookup_pledge
        )
        btn_find.pack(side="left", padx=(0, 10))

        # Main scrollable canvas for full detail & settlement card
        self.canvas = tk.Canvas(self, bg=THEME["bg_main"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_content = tk.Frame(self.canvas, bg=THEME["bg_main"])

        self.scroll_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_win_id = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")

        def _on_canvas_resize(event):
            self.canvas.itemconfig(self.canvas_win_id, width=event.width)

        self.canvas.bind("<Configure>", _on_canvas_resize)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 15))
        self.scrollbar.pack(side="right", fill="y", pady=(0, 15))

        self._show_empty_placeholder()

    def _show_empty_placeholder(self):
        for child in self.scroll_content.winfo_children():
            child.destroy()
        box = tk.Frame(self.scroll_content, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=40, pady=60)
        box.pack(fill="both", expand=True, pady=10)

        tk.Label(
            box,
            text="🔍 Enter a Pledge Number (e.g. A-0001) or Customer Name above to initiate redemption.",
            font=("Segoe UI", 12, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["text_muted"]
        ).pack()

    def lookup_pledge(self):
        query = self.ent_search.get().strip()
        if not query:
            return

        # Try exact pledge_no
        record = PledgeDAO.get_by_pledge_no(query)
        if not record:
            # Try search by name
            res = PledgeDAO.search({"text": query, "status": "ACTIVE"}, limit=1)
            if res:
                record = PledgeDAO.get_by_id(res[0]["id"])

        if not record:
            messagebox.showinfo("Not Found", f"No active pledge found matching '{query}'.")
            return

        self.current_pledge = record
        self._render_release_desk(record)

    def _render_release_desk(self, record):
        """Displays full customer background, photos, anti-fraud connection tree, and settlement."""
        for child in self.scroll_content.winfo_children():
            child.destroy()

        # Check if already released
        if record["status"] == "RELEASED":
            alert_bar = tk.Frame(self.scroll_content, bg="#eff6ff", highlightbackground="#3b82f6", highlightthickness=1, padx=16, pady=10)
            alert_bar.pack(fill="x", pady=(0, 12))
            tk.Label(
                alert_bar,
                text=f"ℹ NOTE: Pledge {record['pledge_no']} was ALREADY RELEASED on {record.get('released_date')} to {record.get('released_to_person')}.",
                font=("Segoe UI", 10, "bold"),
                bg="#eff6ff",
                fg="#1d4ed8"
            ).pack(anchor="w")

        # -------------------------------------------------------------
        # 1. TOP SUMMARY CARD (CUSTOMER & JEWEL WITH PHOTOS)
        # -------------------------------------------------------------
        top_card = tk.Frame(self.scroll_content, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=20, pady=15)
        top_card.pack(fill="x", pady=(0, 15))

        # Title Row
        t_row = tk.Frame(top_card, bg=THEME["bg_card"])
        t_row.pack(fill="x", pady=(0, 10))

        tk.Label(t_row, text=f"PLEDGE {record['pledge_no']}", font=("Segoe UI", 14, "bold"), bg=THEME["bg_card"], fg=THEME["primary_dark"]).pack(side="left")
        tk.Label(t_row, text=f"Pledged on: {record['pledge_date']}  |  Book {record['book_no']}, Entry {record['entry_no']}", font=("Segoe UI", 9), bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(side="left", padx=15)

        # 3-Column Profile Layout:
        # Col 1: Customer Photo & Name, Col 2: Jewel Photo & Details, Col 3: Proofs
        p_grid = tk.Frame(top_card, bg=THEME["bg_card"])
        p_grid.pack(fill="x")
        p_grid.grid_columnconfigure(0, weight=1)
        p_grid.grid_columnconfigure(1, weight=1)

        # Customer Box
        c_box = tk.LabelFrame(p_grid, text=" Customer Background & Identity ", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], padx=10, pady=8)
        c_box.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        c_row = tk.Frame(c_box, bg=THEME["bg_card"])
        c_row.pack(fill="x")

        c_thumb = ImageService.get_thumbnail_path(record.get("customer_photo_path"))
        c_img = ImageService.load_tk_image(c_thumb, size=(75, 85), placeholder_text="👤")
        lbl_c_img = tk.Label(c_row, image=c_img, bg="#f1f5f9", highlightthickness=1, highlightbackground=THEME["border"])
        lbl_c_img.image = c_img
        lbl_c_img.pack(side="left", padx=(0, 10))

        c_txt = tk.Frame(c_row, bg=THEME["bg_card"])
        c_txt.pack(side="left", fill="both", expand=True)

        tk.Label(c_txt, text=record.get("customer_name"), font=("Segoe UI", 11, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        tk.Label(c_txt, text=f"Father/Spouse: {record.get('father_guardian') or 'N/A'}", font=("Segoe UI", 8), bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(anchor="w")
        tk.Label(c_txt, text=f"Phone: {record.get('phone') or 'N/A'}", font=("Segoe UI", 8), bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(anchor="w")
        tk.Label(c_txt, text=f"Aadhaar: {record.get('aadhar') or 'N/A'}", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"], fg=THEME["accent"]).pack(anchor="w")
        tk.Label(c_txt, text=f"Address: {record.get('address') or 'N/A'}", font=("Segoe UI", 8), bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(anchor="w")

        # Jewel Box
        j_box = tk.LabelFrame(p_grid, text=" Pledged Jewel in Vault ", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], padx=10, pady=8)
        j_box.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        j_row = tk.Frame(j_box, bg=THEME["bg_card"])
        j_row.pack(fill="x")

        j_thumb = ImageService.get_thumbnail_path(record.get("jewel_photo_path"))
        j_img = ImageService.load_tk_image(j_thumb, size=(75, 85), placeholder_text="💍")
        lbl_j_img = tk.Label(j_row, image=j_img, bg="#f1f5f9", highlightthickness=1, highlightbackground=THEME["border"])
        lbl_j_img.image = j_img
        lbl_j_img.pack(side="left", padx=(0, 10))

        j_txt = tk.Frame(j_row, bg=THEME["bg_card"])
        j_txt.pack(side="left", fill="both", expand=True)

        jtype = "Gold (G) [2%/g]" if record.get("jewel_type") == "G" else "Silver (S) [3%/g]"
        tk.Label(j_txt, text=record.get("jewel_name"), font=("Segoe UI", 11, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        tk.Label(j_txt, text=f"Type: {jtype} | Hallmark: {record.get('hallmark') or 'Standard'}", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"], fg="#b45309").pack(anchor="w")
        tk.Label(j_txt, text=f"Gross Wt: {record.get('gross_weight')}g  |  Net Wt: {record.get('net_weight')}g", font=("Segoe UI", 8), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        tk.Label(j_txt, text=f"Quantity: {record.get('quantity', 1)} pcs  |  Remarks: {record.get('remarks') or 'Clean'}", font=("Segoe UI", 8), bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(anchor="w")
        tk.Label(j_txt, text=f"Principal Disbursed: ₹ {record.get('principal_amount', 0):,.2f}", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["success"]).pack(anchor="w")

        # -------------------------------------------------------------
        # 2. ANTI-FRAUD VERIFIED CONNECTIONS DISPLAY
        # -------------------------------------------------------------
        conn_frame = tk.LabelFrame(
            self.scroll_content,
            text=" 🛡️ Verified Connection Tree (Verify who is collecting the jewelry) ",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["bg_card"],
            padx=16,
            pady=10
        )
        conn_frame.pack(fill="x", pady=(0, 15))

        tree_view = ConnectionTreeWidget(conn_frame, is_editable=False)
        tree_view.pack(fill="both", expand=True)
        conns = ConnectionDAO.get_for_customer(record["customer_id"])
        tree_view.set_connections(conns)

        # -------------------------------------------------------------
        # 3. SETTLEMENT & INTEREST CALCULATION CARD
        # -------------------------------------------------------------
        settle_card = tk.LabelFrame(
            self.scroll_content,
            text=" 💰 Interest & Redemption Settlement Calculator ",
            font=("Segoe UI", 10, "bold"),
            bg="#fef3c7",
            padx=20,
            pady=15,
            relief="solid",
            borderwidth=1
        )
        settle_card.pack(fill="x", pady=(0, 20))

        s_grid = tk.Frame(settle_card, bg="#fef3c7")
        s_grid.pack(fill="x")
        s_grid.grid_columnconfigure(0, weight=1)
        s_grid.grid_columnconfigure(1, weight=1)

        # Left Column of Settlement
        s_left = tk.Frame(s_grid, bg="#fef3c7")
        s_left.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        # Release Date
        d_row = tk.Frame(s_left, bg="#fef3c7")
        d_row.pack(fill="x", pady=(0, 8))
        tk.Label(d_row, text="Release / Settlement Date:", font=("Segoe UI", 10, "bold"), bg="#fef3c7", fg="#78350f").pack(side="left", padx=(0, 8))
        self.ent_rel_date = ttk.Entry(d_row, width=14, font=("Segoe UI", 10, "bold"))
        self.ent_rel_date.pack(side="left", padx=(0, 6))
        self.ent_rel_date.bind("<KeyRelease>", lambda e: self._recalc_settlement())
        btn_rel_today = tk.Button(
            d_row, text="📅 Today", font=("Segoe UI", 8, "bold"), bg="#e2e8f0", relief="flat", padx=6, pady=2,
            command=lambda: [self.ent_rel_date.delete(0, "end"), self.ent_rel_date.insert(0, date.today().strftime("%Y-%m-%d")), self._recalc_settlement()]
        )
        btn_rel_today.pack(side="left")

        # Released To Person (Anti-Fraud: Must select customer or verified connection!)
        tk.Label(s_left, text="Jewel Handed Over To (Verify with Photo): *", font=("Segoe UI", 10, "bold"), bg="#fef3c7", fg="#78350f").pack(anchor="w")
        receiver_options = [f"{record['customer_name']} (Customer / Owner)"]
        for c in conns:
            receiver_options.append(f"{c['name']} (Verified {c['relation']})")
        receiver_options.append("Authorized Representative (Checked ID Proof)")

        self.cmb_released_to = ttk.Combobox(s_left, values=receiver_options, font=("Segoe UI", 10), state="normal")
        self.cmb_released_to.set("")
        self.cmb_released_to.pack(fill="x", pady=(2, 8))

        # Remarks (NO DEFAULT)
        tk.Label(s_left, text="Release Remarks / Notes:", font=("Segoe UI", 10, "bold"), bg="#fef3c7", fg="#78350f").pack(anchor="w")
        self.ent_rel_remarks = ttk.Entry(s_left, font=("Segoe UI", 10))
        self.ent_rel_remarks.pack(fill="x", pady=(2, 0))

        # Right Column: Calculation Breakdown
        s_right = tk.Frame(s_grid, bg="#fef3c7")
        s_right.grid(row=0, column=1, sticky="nsew", padx=(15, 0))

        self.lbl_days = tk.Label(s_right, text="Days Elapsed: -", font=("Segoe UI", 10, "bold"), bg="#fef3c7", fg="#78350f")
        self.lbl_days.pack(anchor="w", pady=1)

        self.lbl_prin = tk.Label(s_right, text=f"Principal Loan Repayment: ₹ {record.get('principal_amount', 0):,.2f}", font=("Segoe UI", 10), bg="#fef3c7", fg="#78350f")
        self.lbl_prin.pack(anchor="w", pady=1)

        self.lbl_interest = tk.Label(s_right, text="Accrued Interest: ₹ 0.00", font=("Segoe UI", 11, "bold"), bg="#fef3c7", fg="#b45309")
        self.lbl_interest.pack(anchor="w", pady=1)

        # Discount / Concession (NO DEFAULT)
        disc_row = tk.Frame(s_right, bg="#fef3c7")
        disc_row.pack(anchor="w", pady=4)
        tk.Label(disc_row, text="Discount / Concession (₹):", font=("Segoe UI", 10, "bold"), bg="#fef3c7", fg="#78350f").pack(side="left", padx=(0, 6))
        self.ent_discount = ttk.Entry(disc_row, width=12, font=("Segoe UI", 10))
        self.ent_discount.pack(side="left")
        self.ent_discount.bind("<KeyRelease>", lambda e: self._recalc_settlement())

        # Total Net Payable (Big Bold Green Banner)
        self.lbl_net_payable = tk.Label(
            s_right,
            text="TOTAL AMOUNT TO COLLECT: ₹ 0.00",
            font=("Segoe UI", 13, "bold"),
            bg="#dcfce7",
            fg="#15803d",
            padx=10,
            pady=6,
            relief="solid",
            borderwidth=1
        )
        self.lbl_net_payable.pack(fill="x", pady=(8, 0))

        # Action Buttons
        btn_row = tk.Frame(settle_card, bg="#fef3c7")
        btn_row.pack(fill="x", pady=(15, 0))

        if record["status"] == "ACTIVE":
            btn_confirm_release = tk.Button(
                btn_row,
                text="✓ Confirm Release & Generate Receipt (PDF)",
                font=("Segoe UI", 11, "bold"),
                bg=THEME["success"],
                fg="#ffffff",
                relief="flat",
                padx=20,
                pady=10,
                cursor="hand2",
                command=self._confirm_release
            )
            btn_confirm_release.pack(side="left", padx=(0, 15))
        else:
            btn_reprint = tk.Button(
                btn_row,
                text="🖨️ Re-Print Release Receipt (PDF)",
                font=("Segoe UI", 10, "bold"),
                bg="#0284c7",
                fg="#ffffff",
                relief="flat",
                padx=16,
                pady=8,
                cursor="hand2",
                command=self._generate_receipt_pdf
            )
            btn_reprint.pack(side="left")

        # Initial calculation
        self._recalc_settlement()

    def _recalc_settlement(self):
        if not self.current_pledge:
            return
        p_date = self.current_pledge["pledge_date"]
        r_date = self.ent_rel_date.get().strip()
        p_amt = float(self.current_pledge["principal_amount"])
        r_pct = float(self.current_pledge["interest_rate_pct"])
        try:
            disc = float(self.ent_discount.get().strip() or 0)
        except ValueError:
            disc = 0.0

        calc = InterestService.calculate_settlement(p_date, r_date, p_amt, r_pct, discount=disc)
        self.settlement_calc = calc

        self.lbl_days.config(text=f"Days Elapsed: {calc['days_elapsed']} days ({calc['months_billed']} billing months)")
        self.lbl_interest.config(text=f"Accrued Interest: ₹ {calc['accrued_interest']:,.2f} ({r_pct}%/mo)")
        self.lbl_net_payable.config(text=f"TOTAL TO COLLECT: ₹ {calc['net_payable']:,.2f}")

    def _confirm_release(self):
        if not self.current_pledge:
            return

        receiver = self.cmb_released_to.get().strip()
        if not receiver:
            messagebox.showerror("Error", "Please specify who is receiving the jewelry.")
            return

        confirm = messagebox.askyesno(
            "Confirm Redemption",
            f"Are you sure you want to release {self.current_pledge['jewel_name']} to:\n"
            f"👤 {receiver}\n\n"
            f"Total Settlement Collected: ₹ {self.settlement_calc['net_payable']:,.2f}?"
        )
        if not confirm:
            return

        release_payload = {
            "released_date": self.ent_rel_date.get().strip(),
            "released_principal": self.settlement_calc["principal"],
            "released_interest": self.settlement_calc["accrued_interest"],
            "released_discount": self.settlement_calc["discount"],
            "released_total_paid": self.settlement_calc["net_payable"],
            "released_remarks": self.ent_rel_remarks.get().strip(),
            "released_to_person": receiver
        }

        PledgeDAO.release(self.current_pledge["id"], release_payload)
        Toast.show(self.winfo_toplevel(), f"Pledge {self.current_pledge['pledge_no']} successfully redeemed!", "success")

        # Reload updated record
        self.current_pledge = PledgeDAO.get_by_id(self.current_pledge["id"])
        self._generate_receipt_pdf()
        self._render_release_desk(self.current_pledge)

    def _generate_receipt_pdf(self):
        if not self.current_pledge:
            return
        pdf_dir = os.path.join(os.path.expanduser("~"), "Documents")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f"Release_Receipt_{self.current_pledge['pledge_no']}.pdf")
        try:
            ReportService.generate_release_receipt_pdf(self.current_pledge, pdf_path)
            try:
                os.startfile(pdf_path)
            except Exception:
                pass
            messagebox.showinfo("Receipt Generated", f"Redemption receipt created:\n{pdf_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate receipt PDF: {e}")
