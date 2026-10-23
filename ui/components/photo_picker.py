"""
Photo picker component with file browsing, webcam live snapshot, and instant preview.
Optimized for customer portraits, ID proofs, and jewelry snapshots.
Clean responsive sizing with prominent, clearly visible buttons.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2

from config import THEME
from services.image_service import ImageService

class PhotoPicker(tk.Frame):
    def __init__(self, parent, label="Photo", category="customer", preview_size=(150, 165), on_change_callback=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_card"], **kwargs)
        self.label_text = label
        self.category = category
        self.preview_size = preview_size
        self.on_change_callback = on_change_callback
        self.current_image_path = ""
        self.temp_captured_image = None

        self._build_ui()

    def _build_ui(self):
        # Header Label
        lbl = tk.Label(self, text=self.label_text, font=("Segoe UI", 12, "bold"), bg=THEME["bg_card"], fg=THEME["text_dark"], wraplength=320, justify="left")
        lbl.pack(anchor="w", pady=(0, 6))

        # Photo Container Frame with explicit pixel size
        self.box_frame = tk.Frame(
            self,
            bg="#f1f5f9",
            highlightbackground=THEME["border"],
            highlightthickness=1,
            width=self.preview_size[0],
            height=self.preview_size[1]
        )
        self.box_frame.pack_propagate(False)
        self.box_frame.pack(anchor="w", pady=(0, 8))

        self.photo_box = tk.Label(self.box_frame, bg="#f1f5f9")
        self.photo_box.pack(fill="both", expand=True)

        # Action Buttons Row (Bigger, clearly visible)
        btn_frame = tk.Frame(self, bg=THEME["bg_card"])
        btn_frame.pack(anchor="w", fill="x")

        self.btn_browse = tk.Button(
            btn_frame,
            text="📁 Browse",
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg=THEME["text_dark"],
            activebackground="#cbd5e1",
            relief="flat",
            padx=8,
            pady=5,
            cursor="hand2",
            command=self._on_browse_file
        )
        self.btn_browse.pack(side="left", padx=(0, 6))

        self.btn_cam = tk.Button(
            btn_frame,
            text="📷 Camera",
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg=THEME["text_dark"],
            activebackground="#cbd5e1",
            relief="flat",
            padx=8,
            pady=5,
            cursor="hand2",
            command=self._on_capture_webcam
        )
        self.btn_cam.pack(side="left", padx=(0, 6))

        self.btn_clear = tk.Button(
            btn_frame,
            text="✕ Clear",
            font=("Segoe UI", 10, "bold"),
            bg="#fee2e2",
            fg=THEME["danger"],
            activebackground="#fecaca",
            relief="flat",
            padx=8,
            pady=5,
            cursor="hand2",
            command=self.clear_image
        )
        self.btn_clear.pack(side="left")

        self._refresh_preview()

    def _refresh_preview(self):
        icon_text = "👤" if "customer" in self.category or "connection" in self.category else ("🪪" if "id" in self.category else "💍")
        if self.temp_captured_image:
            img = self.temp_captured_image.copy()
            img = img.resize(self.preview_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.photo_box.config(image=photo, text="")
            self.photo_box.image = photo
        elif self.current_image_path and os.path.exists(self.current_image_path):
            photo = ImageService.load_tk_image(self.current_image_path, size=self.preview_size, placeholder_text=icon_text)
            self.photo_box.config(image=photo, text="")
            self.photo_box.image = photo
        else:
            photo = ImageService._create_placeholder(self.preview_size, icon_text)
            self.photo_box.config(image=photo, text="")
            self.photo_box.image = photo

    def _on_browse_file(self):
        path = filedialog.askopenfilename(
            title=f"Select {self.label_text}",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All files", "*.*")]
        )
        if path:
            self.set_image_source(path)

    def _on_capture_webcam(self):
        """Opens a webcam live preview window to take a photo."""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                messagebox.showwarning("Camera Not Found", "No webcam detected or camera access is busy. Please use 'Browse' to select a photo file.")
                return
        except Exception as e:
            messagebox.showwarning("Camera Error", f"Unable to initialize camera: {e}")
            return

        # Webcam Capture Dialog
        win = tk.Toplevel(self)
        win.title("Webcam Capture - Align & Snap")
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
                self.set_image_source(captured["image"])

        btn_snap = tk.Button(
            bottom_bar,
            text="📸 Capture Photo",
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

    def set_image_source(self, path_or_pil):
        if isinstance(path_or_pil, str):
            self.current_image_path = path_or_pil
            self.temp_captured_image = None
        else:
            self.temp_captured_image = path_or_pil
            self.current_image_path = ""

        self._refresh_preview()
        if self.on_change_callback:
            self.on_change_callback(self.get_saved_image_path())

    def get_saved_image_path(self):
        if self.temp_captured_image:
            saved_path = ImageService.save_and_optimize_image(self.temp_captured_image, category=self.category)
            self.current_image_path = saved_path
            self.temp_captured_image = None
            return saved_path
        
        if self.current_image_path:
            if "data" in self.current_image_path and "images" in self.current_image_path:
                return self.current_image_path
            saved_path = ImageService.save_and_optimize_image(self.current_image_path, category=self.category)
            self.current_image_path = saved_path
            return saved_path

        return ""

    def clear_image(self):
        self.current_image_path = ""
        self.temp_captured_image = None
        self._refresh_preview()
        if self.on_change_callback:
            self.on_change_callback("")

    def set_existing_image(self, path):
        self.current_image_path = path or ""
        self.temp_captured_image = None
        self._refresh_preview()
