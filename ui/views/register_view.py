"""
Day Book & Mortgage Register View.
Provides:
- Date-sorted tabular view arranged neatly with multi-criteria filters
- Summary metrics (Totals for Gold wt, Silver wt, Principal, Collections)
- Downloads: Professional PDF Register, Pure Python Genuine Excel (.xlsx), and CSV
- Direct printing support
- One-click backup shortcut
"""
import os
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import THEME, SERIAL_LETTERS
from database.models import PledgeDAO
from services.report_service import ReportService
from services.backup_service import BackupService
from ui.components.toast import Toast

class RegisterView(tk.Frame):
    def __init__(self, parent, navigation_callback, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.navigation_callback = navigation_callback
        self.current_records = []

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # -------------------------------------------------------------
        # TOP FILTER BAR
        # -------------------------------------------------------------
        filter_card = tk.Frame(self, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=20, pady=12)
        filter_card.pack(fill="x", padx=25, pady=(15, 10))

        # Title
        t_row = tk.Frame(filter_card, bg=THEME["bg_card"])
        t_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            t_row,
            text="📋 MORTGAGE REGISTER & DAY BOOK",
            font=("Segoe UI", 12, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["text_dark"]
        ).pack(side="left")

        # Backup button directly available in header
        btn_quick_backup = tk.Button(
            t_row,
            text="💾 Create Instant Backup",
            font=("Segoe UI", 8, "bold"),
            bg=THEME["primary_light"],
            fg=THEME["primary_dark"],
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self._do_quick_backup
        )
        btn_quick_backup.pack(side="right")

        # Filters Row
        f_row = tk.Frame(filter_card, bg=THEME["bg_card"])
        f_row.pack(fill="x")

        # From Date
        tk.Label(f_row, text="From:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(side="left", padx=(0, 4))
        self.ent_from = ttk.Entry(f_row, width=11)
        self.ent_from.pack(side="left", padx=(0, 10))

        # To Date
        tk.Label(f_row, text="To:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(side="left", padx=(0, 4))
        self.ent_to = ttk.Entry(f_row, width=11)
        self.ent_to.pack(side="left", padx=(0, 10))

        # Quick date buttons
        btn_today = tk.Button(f_row, text="Today", font=("Segoe UI", 8), bg="#e2e8f0", relief="flat", padx=6, command=self._set_filter_today)
        btn_today.pack(side="left", padx=(0, 4))

        btn_month = tk.Button(f_row, text="This Month", font=("Segoe UI", 8), bg="#e2e8f0", relief="flat", padx=6, command=self._set_filter_month)
        btn_month.pack(side="left", padx=(0, 4))

        btn_all = tk.Button(f_row, text="All Time", font=("Segoe UI", 8), bg="#e2e8f0", relief="flat", padx=6, command=self._set_filter_all_time)
        btn_all.pack(side="left", padx=(0, 15))

        # Status Filter
        tk.Label(f_row, text="Status:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(side="left", padx=(0, 4))
        self.cmb_status = ttk.Combobox(f_row, values=["ALL", "ACTIVE", "RELEASED"], width=9, state="readonly")
        self.cmb_status.set("ALL")
        self.cmb_status.pack(side="left", padx=(0, 10))

        # Metal Filter
        tk.Label(f_row, text="Type:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(side="left", padx=(0, 4))
        self.cmb_metal = ttk.Combobox(f_row, values=["ALL", "G", "S"], width=5, state="readonly")
        self.cmb_metal.set("ALL")
        self.cmb_metal.pack(side="left", padx=(0, 10))

        # Series Filter
        tk.Label(f_row, text="Series:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(side="left", padx=(0, 4))
        self.cmb_series = ttk.Combobox(f_row, values=["ALL"] + SERIAL_LETTERS, width=5, state="readonly")
        self.cmb_series.set("ALL")
        self.cmb_series.pack(side="left", padx=(0, 15))

        # Filter Submit
        btn_apply = tk.Button(
            f_row,
            text="Filter",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["primary"],
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=3,
            command=self.load_data
        )
        btn_apply.pack(side="left")

        # -------------------------------------------------------------
        # SUMMARY METRIC STRIP
        # -------------------------------------------------------------
        self.summary_strip = tk.Frame(self, bg="#0f172a", padx=18, pady=10)
        self.summary_strip.pack(fill="x", padx=25, pady=(0, 10))

        self.lbl_sum_recs = tk.Label(self.summary_strip, text="Records: 0", font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#ffffff")
        self.lbl_sum_recs.pack(side="left", padx=(0, 20))

        self.lbl_sum_gold = tk.Label(self.summary_strip, text="🪙 Gold: 0.00 g", font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#fbbf24")
        self.lbl_sum_gold.pack(side="left", padx=(0, 20))

        self.lbl_sum_silver = tk.Label(self.summary_strip, text="🥈 Silver: 0.00 g", font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#cbd5e1")
        self.lbl_sum_silver.pack(side="left", padx=(0, 20))

        self.lbl_sum_prin = tk.Label(self.summary_strip, text="Principal: ₹ 0.00", font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#34d399")
        self.lbl_sum_prin.pack(side="left", padx=(0, 20))

        self.lbl_sum_collected = tk.Label(self.summary_strip, text="Collected: ₹ 0.00", font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#38bdf8")
        self.lbl_sum_collected.pack(side="left")

        # -------------------------------------------------------------
        # TABULAR REGISTER
        # -------------------------------------------------------------
        tbl_frame = tk.Frame(self, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1)
        tbl_frame.pack(fill="both", expand=True, padx=25, pady=(0, 10))

        cols = (
            "pledge_no", "date", "book_entry", "customer", "phone", "jewel", "type",
            "net_wt", "principal", "interest_pct", "status", "rel_date", "rel_paid"
        )
        self.tree = ttk.Treeview(tbl_frame, columns=cols, show="headings")

        self.tree.heading("pledge_no", text="Pledge No")
        self.tree.heading("date", text="Date")
        self.tree.heading("book_entry", text="Book/Entry")
        self.tree.heading("customer", text="Customer Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("jewel", text="Jewel Details")
        self.tree.heading("type", text="Type")
        self.tree.heading("net_wt", text="Net Wt (g)")
        self.tree.heading("principal", text="Principal (₹)")
        self.tree.heading("interest_pct", text="Int %")
        self.tree.heading("status", text="Status")
        self.tree.heading("rel_date", text="Release Date")
        self.tree.heading("rel_paid", text="Paid (₹)")

        self.tree.column("pledge_no", width=85, anchor="center")
        self.tree.column("date", width=85, anchor="center")
        self.tree.column("book_entry", width=80, anchor="center")
        self.tree.column("customer", width=140, anchor="w")
        self.tree.column("phone", width=100, anchor="center")
        self.tree.column("jewel", width=140, anchor="w")
        self.tree.column("type", width=50, anchor="center")
        self.tree.column("net_wt", width=75, anchor="e")
        self.tree.column("principal", width=95, anchor="e")
        self.tree.column("interest_pct", width=55, anchor="center")
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("rel_date", width=85, anchor="center")
        self.tree.column("rel_paid", width=90, anchor="e")

        scroll_y = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(tbl_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        tbl_frame.grid_rowconfigure(0, weight=1)
        tbl_frame.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # BOTTOM EXPORT & PRINT ACTIONS
        # -------------------------------------------------------------
        act_card = tk.Frame(self, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=20, pady=12)
        act_card.pack(fill="x", padx=25, pady=(0, 20))

        tk.Label(act_card, text="EXPORT / DOWNLOAD:", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(side="left", padx=(0, 12))

        btn_pdf = tk.Button(
            act_card,
            text="📄 Download PDF Register",
            font=("Segoe UI", 9, "bold"),
            bg="#b91c1c",
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._export_pdf
        )
        btn_pdf.pack(side="left", padx=4)

        btn_excel = tk.Button(
            act_card,
            text="📊 Download Excel (.xlsx)",
            font=("Segoe UI", 9, "bold"),
            bg="#15803d",
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._export_excel
        )
        btn_excel.pack(side="left", padx=4)

        btn_csv = tk.Button(
            act_card,
            text="📑 Download CSV",
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            fg=THEME["text_dark"],
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._export_csv
        )
        btn_csv.pack(side="left", padx=4)

        btn_print = tk.Button(
            act_card,
            text="🖨️ Print Day Book",
            font=("Segoe UI", 9, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._print_daybook
        )
        btn_print.pack(side="right")

    # -------------------------------------------------------------
    # FILTER & DATA LOGIC
    # -------------------------------------------------------------
    def _set_filter_today(self):
        t = date.today().strftime("%Y-%m-%d")
        self.ent_from.delete(0, "end")
        self.ent_from.insert(0, t)
        self.ent_to.delete(0, "end")
        self.ent_to.insert(0, t)
        self.load_data()

    def _set_filter_month(self):
        today = date.today()
        first_day = today.replace(day=1).strftime("%Y-%m-%d")
        self.ent_from.delete(0, "end")
        self.ent_from.insert(0, first_day)
        self.ent_to.delete(0, "end")
        self.ent_to.insert(0, today.strftime("%Y-%m-%d"))
        self.load_data()

    def _set_filter_all_time(self):
        self.ent_from.delete(0, "end")
        self.ent_to.delete(0, "end")
        self.load_data()

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        filters = {
            "from_date": self.ent_from.get().strip(),
            "to_date": self.ent_to.get().strip(),
            "status": self.cmb_status.get(),
            "jewel_type": self.cmb_metal.get(),
            "serial_letter": self.cmb_series.get(),
        }

        records = PledgeDAO.search(filters, limit=5000)
        self.current_records = records

        tot_p = 0.0
        tot_gold = 0.0
        tot_silver = 0.0
        tot_coll = 0.0

        for r in records:
            p_amt = float(r.get("principal_amount", 0))
            net_w = float(r.get("net_weight", 0))
            jtype = r.get("jewel_type", "G")
            paid = float(r.get("released_total_paid") or 0)
            status = r.get("status", "ACTIVE")

            tot_p += p_amt
            tot_coll += paid
            if jtype == "G":
                tot_gold += net_w
            elif jtype == "S":
                tot_silver += net_w

            status_str = "🟢 ACTIVE" if status == "ACTIVE" else "🔵 RELEASED"
            paid_str = f"₹ {paid:,.2f}" if paid > 0 else "-"

            self.tree.insert("", "end", values=(
                r["pledge_no"],
                r["pledge_date"],
                f"B{r['book_no']}-E{r['entry_no']}",
                r["customer_name"],
                r.get("customer_phone", ""),
                r["jewel_name"],
                jtype,
                f"{net_w:.2f}",
                f"₹ {p_amt:,.2f}",
                f"{r.get('interest_rate_pct')}%",
                status_str,
                r.get("released_date") or "-",
                paid_str
            ))

        # Update Summary
        self.lbl_sum_recs.config(text=f"Records: {len(records)}")
        self.lbl_sum_gold.config(text=f"🪙 Gold: {tot_gold:,.2f} g")
        self.lbl_sum_silver.config(text=f"🥈 Silver: {tot_silver:,.2f} g")
        self.lbl_sum_prin.config(text=f"Principal: ₹ {tot_p:,.2f}")
        self.lbl_sum_collected.config(text=f"Collected: ₹ {tot_coll:,.2f}")

    def _export_pdf(self):
        if not self.current_records:
            messagebox.showinfo("Export", "No records found in current filter to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save PDF Register Report",
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")]
        )
        if file_path:
            summary = f"Dates: {self.ent_from.get() or 'All'} to {self.ent_to.get() or 'All'} | Status: {self.cmb_status.get()}"
            try:
                ReportService.generate_register_pdf(self.current_records, summary, file_path)
                try:
                    os.startfile(file_path)
                except Exception:
                    pass
                Toast.show(self.winfo_toplevel(), "PDF Register exported successfully!", "success")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export PDF: {e}")

    def _export_excel(self):
        if not self.current_records:
            messagebox.showinfo("Export", "No records found in current filter to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Excel Spreadsheet",
            defaultextension=".xlsx",
            filetypes=[("Excel Spreadsheet", "*.xlsx")]
        )
        if file_path:
            try:
                ReportService.export_to_excel(self.current_records, file_path)
                try:
                    os.startfile(file_path)
                except Exception:
                    pass
                Toast.show(self.winfo_toplevel(), "Excel (.xlsx) exported successfully!", "success")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export Excel: {e}")

    def _export_csv(self):
        if not self.current_records:
            messagebox.showinfo("Export", "No records found in current filter to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv")]
        )
        if file_path:
            try:
                ReportService.export_to_csv(self.current_records, file_path)
                Toast.show(self.winfo_toplevel(), "CSV exported successfully!", "success")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export CSV: {e}")

    def _print_daybook(self):
        if not self.current_records:
            messagebox.showinfo("Print", "No records to print.")
            return
        temp_dir = os.path.join(os.path.expanduser("~"), "Documents")
        os.makedirs(temp_dir, exist_ok=True)
        pdf_path = os.path.join(temp_dir, f"DayBook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        summary = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        try:
            ReportService.generate_register_pdf(self.current_records, summary, pdf_path)
            try:
                os.startfile(pdf_path)
            except Exception:
                pass
            messagebox.showinfo("Print Ready", f"Day book PDF generated for printing:\n{pdf_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate printable daybook: {e}")

    def _do_quick_backup(self):
        success, path, msg = BackupService.create_backup()
        if success:
            Toast.show(self.winfo_toplevel(), "Backup created successfully!", "success")
            messagebox.showinfo("Backup Successful", f"Full database and images backup created:\n{path}")
        else:
            messagebox.showerror("Backup Error", msg)
