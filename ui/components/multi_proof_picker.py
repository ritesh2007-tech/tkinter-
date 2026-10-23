"""
Multi-Photo Proof Picker Component.
Allows attaching multiple identity proof documents (e.g., Aadhaar Front, Aadhaar Back, PAN card, Voter ID).
Supports file browsing, live webcam snapshots, instant previews, and removals.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2

from config import THEME
from services.image_service import ImageService

class MultiProofPicker(tk.Frame):
    def __init__(self, parent, label="Identity Proof Documents (Multiple Photos Allowed)", card_size=(150, 165), on_change_callback=None, editable=True, **kwargs):
        super().__init__(parent, bg=THEME["bg_card"], **kwargs)
        self.label_text = label
        self.card_size = card_size
        self.on_change_callback = on_change_callback
        self.editable = editable
        self.proof_paths = []  # List of image file paths
        self._thumb_cache = []

        self._build_ui()

    def _build_ui(self):
        # Header Row
        header = tk.Frame(self, bg=THEME["bg_card"])
        header.pack(fill="x", pady=(0, 6))

        lbl_title = tk.Label(
            header,
            text=self.label_text,
            font=("Segoe UI", 12, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["text_dark"],
            wraplength=420,
            justify="left"
        )
        lbl_title.pack(side="left")

        if self.editable:
            btn_box = tk.Frame(header, bg=THEME["bg_card"])
            btn_box.pack(side="right")

            btn_browse = tk.Button(
                btn_box,
                text="📁 Add Photos",
                font=("Segoe UI", 10, "bold"),
                bg="#e2e8f0",
                fg=THEME["text_dark"],
                activebackground="#cbd5e1",
                relief="flat",
                padx=12,
                pady=7,
                cursor="hand2",
                command=self._on_browse_file
            )
            btn_browse.pack(side="left", padx=(0, 6))

            btn_cam = tk.Button(
                btn_box,
                text="📷 Camera",
                font=("Segoe UI", 10, "bold"),
                bg="#e2e8f0",
                fg=THEME["text_dark"],
                activebackground="#cbd5e1",
                relief="flat",
                padx=12,
                pady=7,
                cursor="hand2",
                command=self._on_capture_webcam
            )
            btn_cam.pack(side="left")

        # Container for preview cards
        self.cards_frame = tk.Frame(self, bg=THEME["bg_card"])
        self.cards_frame.pack(fill="x", pady=(4, 0))

        self._refresh_gallery()

    def _refresh_gallery(self):
        for child in self.cards_frame.winfo_children():
            child.destroy()
        self._thumb_cache.clear()

        if not self.proof_paths:
            empty_box = tk.Frame(
                self.cards_frame,
                bg="#f8fafc",
                highlightbackground=THEME["border"],
                highlightthickness=1,
                padx=16,
                pady=14
            )
            empty_box.pack(fill="x")
            lbl = tk.Label(
                empty_box,
                text="🪪 No ID proofs attached yet. Click '📁 Add File' or '📷 Add Camera' to attach Aadhaar (front/back), PAN, Voter ID, etc.",
                font=("Segoe UI", 9, "italic"),
                bg="#f8fafc",
                fg=THEME["text_muted"]
            )
            lbl.pack(fill="x")
            return

        flow_container = tk.Frame(self.cards_frame, bg=THEME["bg_card"])
        flow_container.pack(fill="x")
        flow_container.bind("<Configure>", self._reflow_cards)
        self._flow_container = flow_container

        for idx, path in enumerate(self.proof_paths):
            card = tk.Frame(
                flow_container,
                bg="#ffffff",
                highlightbackground=THEME["border"],
                highlightthickness=1,
                padx=6,
                pady=6
            )
            card.grid(row=0, column=idx, padx=6, pady=4, sticky="nw")

            # Card Header (Index Badge & Delete button)
            c_head = tk.Frame(card, bg="#ffffff")
            c_head.pack(fill="x", pady=(0, 4))

            lbl_badge = tk.Label(
                c_head,
                text=f"Proof #{idx + 1}",
                font=("Segoe UI", 9, "bold"),
                bg=THEME["primary_light"],
                fg=THEME["primary_dark"],
                padx=4,
                pady=1
            )
            lbl_badge.pack(side="left")

            if self.editable:
                btn_del = tk.Button(
                    c_head,
                    text="✕ Remove",
                    font=("Segoe UI", 8, "bold"),
                    bg="#fee2e2",
                    fg=THEME["danger"],
                    relief="flat",
                    padx=4,
                    pady=1,
                    cursor="hand2",
                    command=lambda i=idx: self._remove_proof(i)
                )
                btn_del.pack(side="right")

            # Thumbnail Image Box
            thumb_box = tk.Frame(
                card,
                bg="#f1f5f9",
                width=self.card_size[0],
                height=self.card_size[1]
            )
            thumb_box.pack_propagate(False)
            thumb_box.pack()

            thumb_path = ImageService.get_thumbnail_path(path)
            photo = ImageService.load_tk_image(thumb_path, size=self.card_size, placeholder_text="🪪")
            self._thumb_cache.append(photo)

            lbl_img = tk.Label(thumb_box, image=photo, bg="#f1f5f9", cursor="hand2")
            lbl_img.image = photo
            lbl_img.pack(fill="both", expand=True)
            lbl_img.bind("<Button-1>", lambda e, p=path: self._preview_large(p))
        self.after_idle(self._reflow_cards)

    def _reflow_cards(self, event=None):
        if not hasattr(self, "_flow_container"):
            return
        available_width = event.width if event else self._flow_container.winfo_width()
        card_width = self.card_size[0] + 28
        columns = max(1, available_width // card_width)
        for index, card in enumerate(self._flow_container.winfo_children()):
            card.grid_configure(row=index // columns, column=index % columns)

    def _remove_proof(self, index):
        if 0 <= index < len(self.proof_paths):
            self.proof_paths.pop(index)
            self._refresh_gallery()
            if self.on_change_callback:
                self.on_change_callback(self.proof_paths)

    def _on_browse_file(self):
        paths = filedialog.askopenfilenames(
            title="Select Identity Proof Documents (Multiple Allowed)",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All files", "*.*")]
        )
        if paths:
            for p in paths:
                opt_path = ImageService.save_and_optimize_image(p, category="id_proof")
                if opt_path and opt_path not in self.proof_paths:
                    self.proof_paths.append(opt_path)
            self._refresh_gallery()
            if self.on_change_callback:
                self.on_change_callback(self.proof_paths)

    def _on_capture_webcam(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                messagebox.showwarning("Camera Not Found", "No webcam detected. Please use 'Add File' to select photos.")
                return
        except Exception as e:
            messagebox.showwarning("Camera Error", f"Unable to initialize camera: {e}")
            return

        win = tk.Toplevel(self)
        win.title("Webcam Capture - ID Proof Document")
        win.geometry("580x520")
        win.configure(bg="#0f172a")
        win.resizable(False, False)
        win.grab_set()

        lbl_video = tk.Label(win, bg="#000000")
        lbl_video.pack(fill="both", expand=True, padx=12, pady=12)

        bottom_bar = tk.Frame(win, bg="#0f172a", pady=12)
        bottom_bar.pack(fill="x")

        captured = {"image": None, "running": True}

        def update_frame():
            if not captured["running"]:
                return
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (540, 400))
                pil_img = Image.fromarray(frame_resized)
                tk_img = ImageTk.PhotoImage(pil_img)
                lbl_video.config(image=tk_img)
                lbl_video.image = tk_img
            win.after(30, update_frame)

        def take_snap():
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                captured["image"] = Image.fromarray(frame_rgb)
            close_cam()

        def close_cam():
            captured["running"] = False
            cap.release()
            win.destroy()
            if captured["image"]:
                opt_path = ImageService.save_and_optimize_image(captured["image"], category="id_proof")
                if opt_path:
                    self.proof_paths.append(opt_path)
                    self._refresh_gallery()
                    if self.on_change_callback:
                        self.on_change_callback(self.proof_paths)

        btn_snap = tk.Button(
            bottom_bar,
            text="📸 Capture ID Document",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["primary"],
            fg="#ffffff",
            padx=18,
            pady=8,
            relief="flat",
            command=take_snap
        )
        btn_snap.pack(side="left", padx=25)

        btn_cancel = tk.Button(
            bottom_bar,
            text="Cancel",
            font=("Segoe UI", 10),
            bg="#475569",
            fg="#ffffff",
            padx=14,
            pady=8,
            relief="flat",
            command=close_cam
        )
        btn_cancel.pack(side="right", padx=25)

        win.protocol("WM_DELETE_WINDOW", close_cam)
        update_frame()

    def _preview_large(self, image_path):
        """Opens a larger dialog to view the document in high resolution."""
        if not image_path or not os.path.exists(image_path):
            return
        win = tk.Toplevel(self)
        win.title("Proof Document Preview")
        win.geometry("700x600")
        win.configure(bg="#0f172a")

        photo = ImageService.load_tk_image(image_path, size=(660, 520), placeholder_text="🪪")
        lbl = tk.Label(win, image=photo, bg="#0f172a")
        lbl.image = photo
        lbl.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Button(win, text="Close Preview", font=("Segoe UI", 10, "bold"), bg="#334155", fg="#ffffff", padx=16, pady=6, relief="flat", command=win.destroy).pack(pady=(0, 15))

    def get_proof_paths(self):
        """Returns list of proof photo paths."""
        return list(dict.fromkeys(p for p in self.proof_paths if p and os.path.exists(p)))

    def set_proof_paths(self, path_or_paths):
        """Accepts a single path, a list of paths, or a JSON string."""
        if not path_or_paths:
            self.proof_paths = []
        elif isinstance(path_or_paths, list):
            self.proof_paths = [p for p in path_or_paths if p and os.path.exists(p)]
        elif isinstance(path_or_paths, str):
            p_str = path_or_paths.strip()
            if p_str.startswith("[") and p_str.endswith("]"):
                try:
                    import json
                    parsed = json.loads(p_str)
                    self.proof_paths = [p for p in parsed if isinstance(p, str) and p and os.path.exists(p)] if isinstance(parsed, list) else []
                except json.JSONDecodeError:
                    self.proof_paths = [p_str] if os.path.exists(p_str) else []
            else:
                self.proof_paths = [p_str] if os.path.exists(p_str) else []
        self.proof_paths = list(dict.fromkeys(self.proof_paths))
        self._refresh_gallery()

    def clear(self):
        self.proof_paths = []
        self._refresh_gallery()
