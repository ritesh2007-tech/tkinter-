"""
Connection Network & Relationship Tree Component.
Prevents identity fraud by recording photos, relations, and proof of family/friends/staff.
Visualizes verified relationships so jewelry is never given to an impostor.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME
from services.image_service import ImageService
from ui.components.photo_picker import PhotoPicker

RELATION_OPTIONS = [
    "Sister", "Brother", "Father", "Mother", "Spouse (Wife/Husband)",
    "Son", "Daughter", "Friend", "Staff / Employee", "Business Partner",
    "Uncle / Aunt", "In-law", "Guarantor / Reference", "Other Relative"
]

class ConnectionTreeWidget(tk.Frame):
    def __init__(self, parent, is_editable=True, on_connections_changed=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_card"], **kwargs)
        self.is_editable = is_editable
        self.on_connections_changed = on_connections_changed
        self.connections = []  # List of connection dicts: {name, relation, phone, details, photo_path}
        self._thumb_cache = []

        self._build_ui()

    def _build_ui(self):
        # Header bar
        header = tk.Frame(self, bg=THEME["bg_card"])
        header.pack(fill="x", pady=(0, 6))

        title_lbl = tk.Label(
            header,
            text="👥 Family / Guarantor Connection Tree (Anti-Fraud Proof)",
            font=("Segoe UI", 10, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["text_dark"]
        )
        title_lbl.pack(side="left")

        if self.is_editable:
            btn_add = tk.Button(
                header,
                text="➕ Add Verified Connection",
                font=("Segoe UI", 9, "bold"),
                bg=THEME["primary_light"],
                fg=THEME["primary_dark"],
                relief="flat",
                padx=8,
                pady=2,
                cursor="hand2",
                command=self._open_add_dialog
            )
            btn_add.pack(side="right")

        # Container for connection cards
        self.cards_container = tk.Frame(self, bg=THEME["bg_card"])
        self.cards_container.pack(fill="both", expand=True)

        self._refresh_cards()

    def set_connections(self, conn_list):
        """Sets the connections from database or memory."""
        self.connections = list(conn_list) if conn_list else []
        self._refresh_cards()

    def get_connections(self):
        """Returns the current list of connections."""
        return self.connections

    def _refresh_cards(self):
        for child in self.cards_container.winfo_children():
            child.destroy()
        self._thumb_cache.clear()

        if not self.connections:
            empty_box = tk.Frame(self.cards_container, bg="#f8fafc", highlightbackground=THEME["border"], highlightthickness=1, padx=16, pady=12)
            empty_box.pack(fill="x", pady=4)
            lbl = tk.Label(
                empty_box,
                text="No connections added yet. Add family members, friends, or staff with photos for identity verification.",
                font=("Segoe UI", 9, "italic"),
                bg="#f8fafc",
                fg=THEME["text_muted"]
            )
            lbl.pack()
            return

        # Render connection cards in a clean flow grid
        for idx, conn in enumerate(self.connections):
            card = tk.Frame(
                self.cards_container,
                bg="#ffffff",
                highlightbackground=THEME["border"],
                highlightthickness=1,
                padx=8,
                pady=6
            )
            card.pack(side="left", padx=5, pady=5, anchor="nw")

            # Thumbnail Photo
            photo_path = conn.get("photo_path")
            thumb_path = ImageService.get_thumbnail_path(photo_path) if photo_path else None
            photo = ImageService.load_tk_image(thumb_path, size=(50, 55), placeholder_text="👤")
            self._thumb_cache.append(photo)

            lbl_img = tk.Label(card, image=photo, bg="#f1f5f9", width=50, height=55)
            lbl_img.pack(side="left", padx=(0, 8))

            # Info Frame
            info = tk.Frame(card, bg="#ffffff")
            info.pack(side="left", fill="both")

            lbl_name = tk.Label(info, text=conn["name"], font=("Segoe UI", 9, "bold"), bg="#ffffff", fg=THEME["text_dark"], anchor="w")
            lbl_name.pack(fill="x")

            # Relation Badge
            badge_frame = tk.Frame(info, bg=THEME["primary_light"], padx=4, pady=1)
            badge_frame.pack(anchor="w", pady=2)
            lbl_rel = tk.Label(badge_frame, text=conn["relation"], font=("Segoe UI", 8, "bold"), bg=THEME["primary_light"], fg=THEME["primary_dark"])
            lbl_rel.pack()

            # Phone / Details
            phone_text = conn.get("phone", "") or "No Phone"
            lbl_phone = tk.Label(info, text=f"📞 {phone_text}", font=("Segoe UI", 8), bg="#ffffff", fg=THEME["text_muted"], anchor="w")
            lbl_phone.pack(fill="x")

            if conn.get("details"):
                lbl_det = tk.Label(info, text=conn["details"][:20] + ("..." if len(conn["details"]) > 20 else ""),
                                   font=("Segoe UI", 7, "italic"), bg="#ffffff", fg="#94a3b8", anchor="w")
                lbl_det.pack(fill="x")

            # Remove button if editable
            if self.is_editable:
                btn_del = tk.Button(
                    card,
                    text="✕",
                    font=("Segoe UI", 7, "bold"),
                    bg="#fee2e2",
                    fg=THEME["danger"],
                    relief="flat",
                    padx=4,
                    pady=1,
                    command=lambda i=idx: self._remove_connection(i)
                )
                btn_del.pack(side="right", anchor="ne", padx=(6, 0))

    def _remove_connection(self, index):
        if 0 <= index < len(self.connections):
            self.connections.pop(index)
            self._refresh_cards()
            if self.on_connections_changed:
                self.on_connections_changed(self.connections)

    def _open_add_dialog(self):
        """Opens dialog to enter connection person's details and capture/upload photo."""
        dlg = tk.Toplevel(self)
        dlg.title("Add Verified Connection / Relative")
        dlg.geometry("450x520")
        dlg.configure(bg=THEME["bg_card"])
        dlg.resizable(False, False)
        dlg.grab_set()

        content = tk.Frame(dlg, bg=THEME["bg_card"], padx=20, pady=15)
        content.pack(fill="both", expand=True)

        tk.Label(content, text="Verify Relative / Friend / Staff", font=("Segoe UI", 12, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w", pady=(0, 10))

        # Photo picker for connection
        picker = PhotoPicker(content, label="Connection Photo (Mandatory for Proof)", category="connection", preview_size=(90, 100))
        picker.pack(anchor="w", pady=(0, 10))

        # Fields
        tk.Label(content, text="Full Name *", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        ent_name = ttk.Entry(content, font=("Segoe UI", 10))
        ent_name.pack(fill="x", pady=(0, 8))

        tk.Label(content, text="Relationship *", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        cmb_relation = ttk.Combobox(content, values=RELATION_OPTIONS, font=("Segoe UI", 9), state="readonly")
        cmb_relation.set(RELATION_OPTIONS[0])
        cmb_relation.pack(fill="x", pady=(0, 8))

        tk.Label(content, text="Contact Phone Number", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        ent_phone = ttk.Entry(content, font=("Segoe UI", 10))
        ent_phone.pack(fill="x", pady=(0, 8))

        tk.Label(content, text="Address / Identity Proof Notes", font=("Segoe UI", 9, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"]).pack(anchor="w")
        ent_details = ttk.Entry(content, font=("Segoe UI", 10))
        ent_details.pack(fill="x", pady=(0, 15))

        # Action Buttons
        btn_box = tk.Frame(content, bg=THEME["bg_card"])
        btn_box.pack(fill="x")

        def save_conn():
            name = ent_name.get().strip()
            if not name:
                messagebox.showerror("Required", "Please enter the connection person's name.", parent=dlg)
                return
            
            photo_path = picker.get_saved_image_path()
            relation = cmb_relation.get()
            phone = ent_phone.get().strip()
            details = ent_details.get().strip()

            self.connections.append({
                "name": name,
                "relation": relation,
                "phone": phone,
                "details": details,
                "photo_path": photo_path
            })
            self._refresh_cards()
            if self.on_connections_changed:
                self.on_connections_changed(self.connections)
            dlg.destroy()

        btn_save = tk.Button(
            btn_box,
            text="✓ Save Connection",
            font=("Segoe UI", 10, "bold"),
            bg=THEME["primary"],
            fg="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            command=save_conn
        )
        btn_save.pack(side="left", padx=(0, 10))

        btn_cancel = tk.Button(
            btn_box,
            text="Cancel",
            font=("Segoe UI", 10),
            bg="#e2e8f0",
            fg=THEME["text_dark"],
            relief="flat",
            padx=12,
            pady=6,
            command=dlg.destroy
        )
        btn_cancel.pack(side="left")
