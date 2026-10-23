"""
Customer Directory & Fraud-Prevention Relationship Tree Viewer.
Displays all registered customers, full photo identity proofs, pledge histories,
and visual guarantor/relative connection tree.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from config import THEME
from database.models import CustomerDAO, PledgeDAO, ConnectionDAO
from services.image_service import ImageService
from ui.components.connection_tree import ConnectionTreeWidget
from ui.components.photo_picker import PhotoPicker
from ui.components.multi_proof_picker import MultiProofPicker
from ui.components.toast import Toast

class CustomersView(tk.Frame):
    def __init__(self, parent, navigation_callback, **kwargs):
        super().__init__(parent, bg=THEME["bg_main"], **kwargs)
        self.navigation_callback = navigation_callback
        self.selected_customer = None

        self._build_ui()
        self.load_customers()

    def _build_ui(self):
        # -------------------------------------------------------------
        # TOP HEADER & SEARCH
        # -------------------------------------------------------------
        top_bar = tk.Frame(self, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, padx=20, pady=12)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        tk.Label(
            top_bar,
            text="👥 CUSTOMER DIRECTORY & ANTI-FRAUD CONNECTION NETWORK",
            font=("Segoe UI", 12, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["text_dark"]
        ).pack(anchor="w", pady=(0, 8))

        s_row = tk.Frame(top_bar, bg=THEME["bg_card"])
        s_row.pack(fill="x")

        tk.Label(s_row, text="Search Customer (Name / Phone / Aadhaar):", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"]).pack(side="left", padx=(0, 8))
        self.ent_search = ttk.Entry(s_row, width=30, font=("Segoe UI", 10))
        self.ent_search.pack(side="left", padx=(0, 10))
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_customers())

        btn_refresh = tk.Button(s_row, text="🔄 Refresh", font=("Segoe UI", 9), bg="#e2e8f0", relief="flat", padx=10, pady=3, command=self.load_customers)
        btn_refresh.pack(side="left")

        # -------------------------------------------------------------
        # MAIN 2-PANE: LIST ON LEFT, FULL PROFILE & CONNECTION TREE ON RIGHT
        # -------------------------------------------------------------
        paned = tk.PanedWindow(self, orient="horizontal", bg=THEME["bg_main"], sashwidth=4)
        paned.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # Left: Customer List
        list_frame = tk.Frame(paned, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1)
        paned.add(list_frame, width=420)

        cols = ("id", "name", "phone", "aadhar")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("aadhar", text="Aadhaar No")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("name", width=140, anchor="w")
        self.tree.column("phone", width=105, anchor="center")
        self.tree.column("aadhar", width=115, anchor="center")

        scroll_y = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select_customer)

        # Right: Profile & Connection Details Pane
        self.detail_frame = tk.Frame(paned, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1)
        paned.add(self.detail_frame, width=620)

        self._show_empty_detail()

    def _show_empty_detail(self):
        for child in self.detail_frame.winfo_children():
            child.destroy()
        lbl = tk.Label(
            self.detail_frame,
            text="👈 Select a customer from the directory to inspect photo identity proofs, pledge history, and verified connections.",
            font=("Segoe UI", 10, "italic"),
            bg=THEME["bg_card"],
            fg=THEME["text_muted"],
            wraplength=450,
            justify="center"
        )
        lbl.pack(expand=True, padx=20)

    def load_customers(self):
        query = self.ent_search.get().strip()
        for item in self.tree.get_children():
            self.tree.delete(item)

        results = CustomerDAO.search(query, limit=100) if query else CustomerDAO.search("", limit=200)
        for c in results:
            self.tree.insert("", "end", values=(
                c["id"],
                c["name"],
                c.get("phone") or "-",
                c.get("aadhar") or "-"
            ))

    def _on_select_customer(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        if not vals:
            return
        cust_id = vals[0]
        cust = CustomerDAO.get_by_id(cust_id)
        if cust:
            self.selected_customer = cust
            self._render_customer_profile(cust)

    def _render_customer_profile(self, cust):
        for child in self.detail_frame.winfo_children():
            child.destroy()

        canvas = tk.Canvas(self.detail_frame, bg=THEME["bg_card"], highlightthickness=0)
        scroll = ttk.Scrollbar(self.detail_frame, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg=THEME["bg_card"], padx=16, pady=12)

        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(content_window, width=e.width))
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Top Profile Banner
        p_row = tk.Frame(content, bg="#f8fafc", highlightbackground=THEME["border"], highlightthickness=1, padx=12, pady=10)
        p_row.pack(fill="x", pady=(0, 12))

        # Photos
        c_thumb = ImageService.get_thumbnail_path(cust.get("photo_path"))
        c_img = ImageService.load_tk_image(c_thumb, size=(105, 120), placeholder_text="👤")
        lbl_c_img = tk.Label(p_row, image=c_img, bg="#ffffff", highlightthickness=1, highlightbackground=THEME["border"])
        lbl_c_img.image = c_img
        lbl_c_img.pack(side="left", padx=(0, 10))

        # Text Details
        txt_box = tk.Frame(p_row, bg="#f8fafc")
        txt_box.pack(side="left", fill="both", expand=True)

        tk.Label(txt_box, text=cust["name"], font=("Segoe UI", 15, "bold"), bg="#f8fafc", fg=THEME["text_dark"], wraplength=360, justify="left").pack(anchor="w")
        tk.Label(txt_box, text=f"Father / Spouse: {cust.get('father_guardian') or 'N/A'}", font=("Segoe UI", 10), bg="#f8fafc", fg=THEME["text_muted"], wraplength=360, justify="left").pack(anchor="w")
        tk.Label(txt_box, text=f"📞 Phone: {cust.get('phone') or 'N/A'}", font=("Segoe UI", 10), bg="#f8fafc", fg=THEME["text_dark"], wraplength=360, justify="left").pack(anchor="w")
        tk.Label(txt_box, text=f"🪪 Aadhaar: {cust.get('aadhar') or 'N/A'}", font=("Segoe UI", 10, "bold"), bg="#f8fafc", fg=THEME["accent"], wraplength=360, justify="left").pack(anchor="w")
        tk.Label(txt_box, text=f"📍 Address: {cust.get('address') or 'N/A'}", font=("Segoe UI", 10), bg="#f8fafc", fg=THEME["text_muted"], wraplength=360, justify="left").pack(anchor="w")

        proof_gallery = MultiProofPicker(
            content,
            label="Identity Proof Photos",
            card_size=(105, 115),
            editable=False
        )
        proof_gallery.pack(fill="x", pady=(0, 12))
        proof_gallery.set_proof_paths(CustomerDAO.get_proof_photos(cust))

        # Verified Relatives Connection Tree
        c_tree_box = tk.LabelFrame(
            content,
            text=" 🛡️ Verified Connection Tree (Anti-Impostor Verification) ",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["bg_card"],
            padx=12,
            pady=10
        )
        c_tree_box.pack(fill="x", pady=(0, 12))

        conns = ConnectionDAO.get_for_customer(cust["id"])
        tree_widget = ConnectionTreeWidget(
            c_tree_box,
            is_editable=True,
            on_connections_changed=lambda clist: self._sync_connections(cust["id"], clist)
        )
        tree_widget.pack(fill="both", expand=True)
        tree_widget.set_connections(conns)

        # Mortgage History Table
        hist_box = tk.LabelFrame(content, text=" Customer Mortgage & Pledge History ", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], padx=10, pady=8)
        hist_box.pack(fill="x", pady=(0, 15))

        pledges = PledgeDAO.search({"text": cust["name"]}, limit=50)
        # Filter for exact customer_id
        customer_pledges = [p for p in pledges if p["customer_id"] == cust["id"]]

        if customer_pledges:
            for p in customer_pledges:
                p_row_f = tk.Frame(hist_box, bg="#ffffff", highlightbackground=THEME["border"], highlightthickness=1, padx=8, pady=4)
                p_row_f.pack(fill="x", pady=2)

                status_color = THEME["success"] if p["status"] == "ACTIVE" else THEME["accent"]
                status_icon = "🟢 ACTIVE" if p["status"] == "ACTIVE" else "🔵 RELEASED"

                tk.Label(p_row_f, text=p["pledge_no"], font=("Segoe UI", 9, "bold"), bg="#ffffff", fg=THEME["primary_dark"]).pack(side="left", padx=(0, 10))
                tk.Label(p_row_f, text=p["pledge_date"], font=("Segoe UI", 8), bg="#ffffff", fg=THEME["text_muted"]).pack(side="left", padx=(0, 10))
                tk.Label(p_row_f, text=f"{p['jewel_name']} ({p['net_weight']}g)", font=("Segoe UI", 8), bg="#ffffff", fg=THEME["text_dark"]).pack(side="left", padx=(0, 10))
                tk.Label(p_row_f, text=f"₹ {p['principal_amount']:,.2f}", font=("Segoe UI", 8, "bold"), bg="#ffffff", fg=THEME["text_dark"]).pack(side="left", padx=(0, 10))
                tk.Label(p_row_f, text=status_icon, font=("Segoe UI", 8, "bold"), bg="#ffffff", fg=status_color).pack(side="right")
        else:
            tk.Label(hist_box, text="No pledges found for this customer.", font=("Segoe UI", 8, "italic"), bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(pady=4)

        # Customer Actions
        act_row = tk.Frame(content, bg=THEME["bg_card"])
        act_row.pack(fill="x")

        btn_new_p = tk.Button(
            act_row,
            text="➕ New Pledge for this Customer",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["primary"],
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.navigation_callback("new_entry")
        )
        btn_new_p.pack(side="left", padx=(0, 8))

        btn_del_c = tk.Button(
            act_row,
            text="🗑️ Delete Customer",
            font=("Segoe UI", 9),
            bg="#fee2e2",
            fg=THEME["danger"],
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=lambda: self._delete_customer(cust)
        )
        btn_del_c.pack(side="right")

    def _sync_connections(self, cust_id, connection_list):
        """Saves newly added connections from tree widget to DB."""
        for c in connection_list:
            if not c.get("id"):
                ConnectionDAO.add(cust_id, c["name"], c["relation"], c.get("phone", ""), c.get("details", ""), c.get("photo_path", ""))
        Toast.show(self.winfo_toplevel(), "Connection tree updated!", "success")

    def _delete_customer(self, cust):
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete customer {cust['name']}?\n(Note: Can only be deleted if no active pledges exist).")
        if not confirm:
            return
        try:
            CustomerDAO.delete(cust["id"])
            Toast.show(self.winfo_toplevel(), "Customer deleted successfully.", "success")
            self.load_customers()
            self._show_empty_detail()
        except ValueError as e:
            messagebox.showerror("Cannot Delete", str(e))
