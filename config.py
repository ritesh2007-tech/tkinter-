"""
Configuration and constants for the Jewelry Mortgage System.
"""
import os
import sys

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
DB_PATH = os.path.join(DATA_DIR, "jewelry_mortgage.db")

# Subdirectories for organized image storage
IMG_CUSTOMERS_DIR = os.path.join(IMAGES_DIR, "customers")
IMG_ID_PROOFS_DIR = os.path.join(IMAGES_DIR, "id_proofs")
IMG_JEWELS_DIR = os.path.join(IMAGES_DIR, "jewels")
IMG_CONNECTIONS_DIR = os.path.join(IMAGES_DIR, "connections")
IMG_THUMBNAILS_DIR = os.path.join(IMAGES_DIR, "thumbnails")

# Ensure required directories exist
for folder in [
    DATA_DIR,
    IMAGES_DIR,
    BACKUP_DIR,
    IMG_CUSTOMERS_DIR,
    IMG_ID_PROOFS_DIR,
    IMG_JEWELS_DIR,
    IMG_CONNECTIONS_DIR,
    IMG_THUMBNAILS_DIR,
]:
    os.makedirs(folder, exist_ok=True)

# Application Info
APP_NAME = "SwarnaRatna Jewelry Mortgage & Pledge System"
APP_SUBTITLE = "Smart & Secure Pawn Broking Management System"
APP_VERSION = "2.0.0"

# Default Business Rules
DEFAULT_SHOP_NAME = "SWARNA RATNA JEWEL MORTGAGE BANKERS"
DEFAULT_SHOP_ADDRESS = "108, Bazaar Main Road, Gold Market Complex"
DEFAULT_SHOP_PHONE = "+91 98765 43210 / 044-24567890"
DEFAULT_SHOP_LICENSE = "PAWN/LIC/2026/G-8872"
DEFAULT_SHOP_GSTIN = "33AAAAA0000A1Z5"

# Interest Configuration (Per specifications: Gold 2%, Silver 3%)
# Gold: 2.0% per month or based on per gram calculation
# Silver: 3.0% per month or based on per gram calculation
DEFAULT_GOLD_RATE_PCT = 2.0  # 2% interest per month / per gram reference
DEFAULT_SILVER_RATE_PCT = 3.0  # 3% interest per month / per gram reference

# Serial System Configuration
# Serial letter: A to Z
# Serial number: 1 to 9999 per letter
# 1 Serial Letter = 100 Books, 1 Book = 100 Entries (10,000 total)
SERIAL_LETTERS = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
MAX_SERIAL_PER_LETTER = 9999
ENTRIES_PER_BOOK = 100
BOOKS_PER_LETTER = 100

# Security Defaults
DEFAULT_ADMIN_PIN = "1234"  # Can be changed in settings

# Theme Palette (Modern Elegant Slate & Gold)
THEME = {
    "bg_main": "#f8fafc",         # Very light slate canvas
    "bg_card": "#ffffff",         # Pure white cards
    "bg_sidebar": "#0f172a",      # Deep dark slate navy
    "bg_sidebar_hover": "#1e293b",# Slate hover
    "bg_sidebar_active": "#334155",
    "primary": "#d97706",         # Warm amber gold
    "primary_dark": "#b45309",    # Deep gold
    "primary_light": "#fef3c7",   # Soft gold tint
    "accent": "#2563eb",          # Royal blue for links & secondary actions
    "accent_light": "#eff6ff",
    "text_dark": "#0f172a",       # Slate 900
    "text_muted": "#64748b",      # Slate 500
    "text_light": "#f8fafc",      # Slate 50
    "border": "#e2e8f0",          # Slate 200
    "border_focus": "#d97706",    # Gold focus
    "success": "#16a34a",         # Emerald green for active/released
    "success_bg": "#dcfce7",
    "warning": "#ea580c",         # Orange
    "warning_bg": "#ffedd5",
    "danger": "#dc2626",          # Crimson red for delete/overdue
    "danger_bg": "#fee2e2",
    "info": "#0284c7",            # Sky blue
    "info_bg": "#e0f2fe",
}

# Image Optimization Settings
MAX_IMAGE_DIMENSION = 800         # Max width/height for full photo
THUMBNAIL_DIMENSION = 140         # Max width/height for thumbnail
IMAGE_JPEG_QUALITY = 85           # Balanced quality & fast loading
THUMBNAIL_JPEG_QUALITY = 75
