"""
Settings, Security, Backup & Audit Trail View.
Manages:
- Shop Profile & License details (printed on receipts and pledges)
- Interest rates defaults (Gold 2%, Silver 3%)
- Admin PIN for security operations
- Complete Backup and Restore operations (DB + Photos)
- System Audit Logs
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from config import THEME, SERIAL_LETTERS
from database.models import SettingsDAO, AuditDAO
from services.backup_service import BackupService
from ui.components.toast import Toast

class SettingsView(tk.Frame):
    def __init__(self, parent, navigation_callback, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.navigation_callback = navigation_callback

        self._build_ui()
        self.load_settings()

    def _build_ui(self):
        canvas = tk.Canvas(self, bg=THEME["bg_main"], highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg=THEME["bg_main"], padx=25, pady=15)

        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self.canvas_win_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_settings_resize(e):
            canvas.itemconfig(self.canvas_win_id, width=e.width)

        canvas.bind("<Configure>", _on_settings_resize)
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # -------------------------------------------------------------
        # 1. SHOP PROFILE & PRINT HEADER SETTINGS
        # -------------------------------------------------------------
        shop_card = tk.LabelFrame(content, text=" 🏬 Shop Profile & Voucher Header Configuration ", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], padx=18, pady=14)
        shop_card.pack(fill="x", pady=(0, 15))

        tk.Label(shop_card, text="Business / Shop Name *", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        self.ent_shop_name = ttk.Entry(shop_card, font=("Segoe UI", 10))
        self.ent_shop_name.pack(fill="x", pady=(2, 8))

        row_la = tk.Frame(shop_card, bg=THEME["bg_card"])
        row_la.pack(fill="x", pady=(0, 8))
        row_la.grid_columnconfigure(0, weight=1)
        row_la.grid_columnconfigure(1, weight=1)

        c_a = tk.Frame(row_la, bg=THEME["bg_card"])
        c_a.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        tk.Label(c_a, text="Shop Address", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        self.ent_shop_address = ttk.Entry(c_a)
        self.ent_shop_address.pack(fill="x", pady=(2, 0))

        c_p = tk.Frame(row_la, bg=THEME["bg_card"])
        c_p.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        tk.Label(c_p, text="Contact Phone Numbers", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        self.ent_shop_phone = ttk.Entry(c_p)
        self.ent_shop_phone.pack(fill="x", pady=(2, 0))

        row_lg = tk.Frame(shop_card, bg=THEME["bg_card"])
        row_lg.pack(fill="x", pady=(0, 10))
        row_lg.grid_columnconfigure(0, weight=1)
        row_lg.grid_columnconfigure(1, weight=1)

        c_lic = tk.Frame(row_lg, bg=THEME["bg_card"])
        c_lic.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        tk.Label(c_lic, text="Pawn Broker License No", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        self.ent_shop_license = ttk.Entry(c_lic)
        self.ent_shop_license.pack(fill="x", pady=(2, 0))

        c_gst = tk.Frame(row_lg, bg=THEME["bg_card"])
        c_gst.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        tk.Label(c_gst, text="GSTIN / Tax ID", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        self.ent_shop_gstin = ttk.Entry(c_gst)
        self.ent_shop_gstin.pack(fill="x", pady=(2, 0))

        # -------------------------------------------------------------
        # 2. DEFAULT INTEREST RATES & SERIAL SETTINGS
        # -------------------------------------------------------------
        rate_card = tk.LabelFrame(content, text=" ⚙️ Interest Rates & Serial System Configuration ", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], padx=18, pady=14)
        rate_card.pack(fill="x", pady=(0, 15))

        r_grid = tk.Frame(rate_card, bg=THEME["bg_card"])
        r_grid.pack(fill="x")
        r_grid.grid_columnconfigure(0, weight=1)
        r_grid.grid_columnconfigure(1, weight=1)
        r_grid.grid_columnconfigure(2, weight=1)

        c_g = tk.Frame(r_grid, bg=THEME["bg_card"])
        c_g.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        tk.Label(c_g, text="Gold Interest Rate (% / Month / g)", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        self.ent_gold_rate = ttk.Entry(c_g)
        self.ent_gold_rate.pack(fill="x", pady=(2, 0))

        c_s = tk.Frame(r_grid, bg=THEME["bg_card"])
        c_s.grid(row=0, column=1, sticky="ew", padx=6)
        tk.Label(c_s, text="Silver Interest Rate (% / Month / g)", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        self.ent_silver_rate = ttk.Entry(c_s)
        self.ent_silver_rate.pack(fill="x", pady=(2, 0))

        c_ser = tk.Frame(r_grid, bg=THEME["bg_card"])
        c_ser.grid(row=0, column=2, sticky="ew", padx=(6, 0))
        tk.Label(c_ser, text="Current Active Series Letter", font=("Segoe UI", 8, "bold"), bg=THEME["bg_card"]).pack(anchor="w")
        self.cmb_active_series = ttk.Combobox(c_ser, values=SERIAL_LETTERS, state="readonly")
        self.cmb_active_series.pack(fill="x", pady=(2, 0))

        # -------------------------------------------------------------
        # 3. SECURITY & ADMIN PIN
        # -------------------------------------------------------------
        sec_card = tk.LabelFrame(content, text=" 🔒 Security PIN & Access Protection ", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], padx=18, pady=14)
        sec_card.pack(fill="x", pady=(0, 15))

        sec_row = tk.Frame(sec_card, bg=THEME["bg_card"])
        sec_row.pack(fill="x")

        tk.Label(sec_row, text="Admin Security PIN (for deletions & restores):", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(side="left", padx=(0, 10))
        self.ent_admin_pin = ttk.Entry(sec_row, show="*", width=12, font=("Segoe UI", 10, "bold"))
        self.ent_admin_pin.pack(side="left", padx=(0, 20))

        btn_save_settings = tk.Button(
            sec_card,
            text="💾 Save Configuration",
            font=("Segoe UI", 10, "bold"),
            bg=THEME["primary"],
            fg="#ffffff",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=self._save_settings
        )
        btn_save_settings.pack(anchor="w", pady=(10, 0))

        # -------------------------------------------------------------
        # 4. BACKUP & RESTORE SECTION
        # -------------------------------------------------------------
        bkp_card = tk.LabelFrame(content, text=" 💾 Backup & Disaster Recovery (Offline Scalable Storage) ", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], padx=18, pady=14)
        bkp_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            bkp_card,
            text="Create full offline backup archives containing the SQLite database and all compressed photo proofs.\nRestore backups safely with automatic rollback protection.",
            font=("Segoe UI", 8),
            bg=THEME["bg_card"],
            fg=THEME["text_muted"],
            justify="left"
        ).pack(anchor="w", pady=(0, 12))

        b_row = tk.Frame(bkp_card, bg=THEME["bg_card"])
        b_row.pack(fill="x")

        btn_backup = tk.Button(
            b_row,
            text="💾 Create Full System Backup (.zip)",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["success"],
            fg="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._create_backup
        )
        btn_backup.pack(side="left", padx=(0, 12))

        btn_restore = tk.Button(
            b_row,
            text="📥 Restore Database from Backup",
            font=("Segoe UI", 9, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._restore_backup
        )
        btn_restore.pack(side="left")

        # -------------------------------------------------------------
        # 5. AUDIT LOG VIEWER
        # -------------------------------------------------------------
        audit_card = tk.LabelFrame(content, text=" 📜 Security Audit Trail & Operation Logs ", font=("Segoe UI", 10, "bold"), bg=THEME["bg_card"], padx=18, pady=14)
        audit_card.pack(fill="x", pady=(0, 20))

        cols = ("id", "action", "ref", "details", "time")
        self.audit_tree = ttk.Treeview(audit_card, columns=cols, show="headings", height=6)

        self.audit_tree.heading("id", text="#")
        self.audit_tree.heading("action", text="Action")
        self.audit_tree.heading("ref", text="Reference")
        self.audit_tree.heading("details", text="Details")
        self.audit_tree.heading("time", text="Timestamp")

        self.audit_tree.column("id", width=40, anchor="center")
        self.audit_tree.column("action", width=120, anchor="center")
        self.audit_tree.column("ref", width=90, anchor="center")
        self.audit_tree.column("details", width=380, anchor="w")
        self.audit_tree.column("time", width=140, anchor="center")

        self.audit_tree.pack(fill="x")

    def load_settings(self):
        settings = SettingsDAO.get_all()
        self.ent_shop_name.delete(0, "end")
        self.ent_shop_name.insert(0, settings.get("shop_name", ""))

        self.ent_shop_address.delete(0, "end")
        self.ent_shop_address.insert(0, settings.get("shop_address", ""))

        self.ent_shop_phone.delete(0, "end")
        self.ent_shop_phone.insert(0, settings.get("shop_phone", ""))

        self.ent_shop_license.delete(0, "end")
        self.ent_shop_license.insert(0, settings.get("shop_license", ""))

        self.ent_shop_gstin.delete(0, "end")
        self.ent_shop_gstin.insert(0, settings.get("shop_gstin", ""))

        self.ent_gold_rate.delete(0, "end")
        self.ent_gold_rate.insert(0, settings.get("gold_rate_pct", "2.0"))

        self.ent_silver_rate.delete(0, "end")
        self.ent_silver_rate.insert(0, settings.get("silver_rate_pct", "3.0"))

        self.cmb_active_series.set(settings.get("current_serial_letter", "A"))

        self.ent_admin_pin.delete(0, "end")
        self.ent_admin_pin.insert(0, settings.get("admin_pin", "1234"))

        # Load audit logs
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)

        logs = AuditDAO.get_recent(limit=30)
        for l in logs:
            self.audit_tree.insert("", "end", values=(
                l["id"],
                l["action_type"],
                l.get("reference_id") or "-",
                l["details"],
                l["created_at"]
            ))

    def _save_settings(self):
        SettingsDAO.set("shop_name", self.ent_shop_name.get().strip())
        SettingsDAO.set("shop_address", self.ent_shop_address.get().strip())
        SettingsDAO.set("shop_phone", self.ent_shop_phone.get().strip())
        SettingsDAO.set("shop_license", self.ent_shop_license.get().strip())
        SettingsDAO.set("shop_gstin", self.ent_shop_gstin.get().strip())
        SettingsDAO.set("gold_rate_pct", self.ent_gold_rate.get().strip())
        SettingsDAO.set("silver_rate_pct", self.ent_silver_rate.get().strip())
        SettingsDAO.set("current_serial_letter", self.cmb_active_series.get().strip())
        SettingsDAO.set("admin_pin", self.ent_admin_pin.get().strip())

        AuditDAO.log("SETTINGS_UPDATED", "SYSTEM", "Business and security settings updated")
        Toast.show(self.winfo_toplevel(), "Settings updated successfully!", "success")
        self.load_settings()

    def _create_backup(self):
        dest_folder = filedialog.askdirectory(title="Select Destination Folder for Backup")
        if dest_folder:
            success, path, msg = BackupService.create_backup(dest_folder)
            if success:
                Toast.show(self.winfo_toplevel(), "Backup created successfully!", "success")
                messagebox.showinfo("Backup Complete", f"Backup archive saved to:\n{path}")
                self.load_settings()
            else:
                messagebox.showerror("Backup Error", msg)

    def _restore_backup(self):
        curr_pin = SettingsDAO.get("admin_pin", "1234")
        entered_pin = self.ent_admin_pin.get().strip()
        if entered_pin != curr_pin:
            messagebox.showerror("Access Denied", "Please enter the correct Admin PIN in the security field first.")
            return

        zip_file = filedialog.askopenfilename(
            title="Select Backup ZIP Archive to Restore",
            filetypes=[("Zip files", "*.zip")]
        )
        if not zip_file:
            return

        confirm = messagebox.askyesno(
            "Confirm Dangerous Operation",
            "Restoring a backup will overwrite existing database records and replace image files.\nAre you sure you want to proceed?"
        )
        if not confirm:
            return

        success, msg = BackupService.restore_backup(zip_file)
        if success:
            Toast.show(self.winfo_toplevel(), "Database restored successfully!", "success")
            messagebox.showinfo("Restore Complete", f"{msg}\nApplication will now reload settings.")
            self.load_settings()
        else:
            messagebox.showerror("Restore Failed", msg)
