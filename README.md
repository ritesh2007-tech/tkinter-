# SwarnaRatna - Modern Jewelry Mortgage & Pledge System (Python Tkinter & SQLite)

An enterprise-grade, offline-first desktop application engineered specifically for **Jewelry Mortgage / Pawn Broking Bankers**. Built with Python, Tkinter (Modern Flat TTK styling), SQLite (WAL mode with performance indexing), Pillow (dynamic image optimization and compression), and ReportLab (PDF vouchers and registers).

---

## 🌟 Key Features

### 1. New Pledge Entry
- **Serial System (A-Z & 1-9999)**:
  - Supports Serial letters **A to Z** and numbers **1 to 9999** per letter.
  - Automatically calculates **Book Number (1 to 100)** and **Entry Number (1 to 100)** based on the 100 books $\times$ 100 entries per letter standard (10,000 capacity per letter).
  - Auto-increments to the next available pledge number (e.g. `A-0001`, `A-0002`) with manual entry validation.
- **Date Handling**:
  - Automatically loads system date (`YYYY-MM-DD`).
  - Includes safe manual date override for back-dated entries with format validation.
- **Customer Auto-Detect & Shortcut Lookup**:
  - As you type the customer name, phone, or Aadhaar, an instant dropdown with the customer's photo thumbnail, phone, and address appears.
  - Selecting an existing customer auto-fills their details, photos, and existing connections.
  - If a new name is typed, it automatically registers as a new customer without extra steps.
- **Customer Identity Proofs**:
  - Customer Portrait Photo (Webcam live capture or file browse).
  - Aadhaar / ID Proof Document photo.
  - Father / Husband / Guardian name, residential address, contact number, Aadhaar number.
- **Jewelry Details**:
  - Jewel Description (e.g., Gold Chain, Ring, Bangle, Necklace, Anklets).
  - Metal Type: **🪙 Gold (G)** or **🥈 Silver (S)**.
  - Gross Weight and Net Weight (grams).
  - Quantity (pieces), Hallmark stamp (`916 BIS`, `22K`, `Silver 925`, etc.), and Condition remarks.
  - Principal Loan Amount (Cash given in ₹).
- **Automated Interest Calculation**:
  - **Gold**: Auto-computes at **2.0% interest per month / per gram reference**.
  - **Silver**: Auto-computes at **3.0% interest per month / per gram reference**.
  - Displays real-time breakdown of Monthly Interest Amount (₹), Annual Percentage Rate, and per-gram interest rate factor as you type.
- **🛡️ Anti-Fraud Connection Tree (Guarantor / Relative Network)**:
  - Allows attaching verified relatives, friends, or staff members to each customer profile.
  - Captures the connection person's **Photo**, **Full Name**, **Relationship** (Sister, Brother, Father, Mother, Spouse, Friend, Staff, etc.), **Contact Phone**, and **ID proof notes**.
  - Visual tree display prevents fraud (such as impostors pretending to be family members attempting to redeem or claim pledged jewelry).

---

### 2. Search, History & Full Updation / Deletion
- **Multi-Criteria Search**:
  - Instant live search across Pledge Number, Customer Name, Phone, Aadhaar, and Jewel description.
  - Filter by Status (`ALL`, `ACTIVE` in vault, `RELEASED`), Metal (`ALL`, `Gold`, `Silver`), and Series Letter (`ALL`, `A-Z`).
- **Full Profile Inspector**:
  - Displays customer portrait photo, ID card proof, and jewel snapshot side-by-side.
  - Visual Connection Tree for fraud verification.
  - Status indicators (🟢 ACTIVE in vault / 🔵 RELEASED).
- **Comprehensive Updation & Editing**:
  - Update any field: Customer name, guardian, address, phone, Aadhaar.
  - Replace/update photos: Customer photo, ID proof photo, Jewel photo.
  - Update weights, principal amount, interest rate, hallmark, and condition remarks.
  - Add or update verified connections in the tree.
- **Secure Deletion**:
  - Protected with an **Admin Security PIN** to prevent accidental or unauthorized data loss.

---

### 3. Release Jewelry / Redemption Desk
- **Fast Lookup**:
  - Search by Pledge Number (e.g. `A-0001`) or Customer Name.
- **Background & Fraud Verification**:
  - Displays full customer photo, jewel details, and verified connections.
  - Required field: **"Jewel Handed Over To"** (must select verified customer or photo-verified connection person).
- **Automated Redemption Settlement Calculator**:
  - Calculates exact days elapsed and billing months between pledge date and release date.
  - Auto-calculates total accrued interest (minimum 1-month pawn broking rule or exact pro-rata).
  - Supports Discount / Concession adjustment.
  - Computes exact Net Settlement Amount to collect.
- **Release Voucher**:
  - Marks pledge as `RELEASED` in the database.
  - Generates a professional **PDF Release Receipt** for printing and customer signature.

---

### 4. Register & Reports (Day Book)
- **Neat Data Arrangement**:
  - Formatted tabular view sorted by pledge date, book number, and entry number.
  - Summary metrics bar: Total Entries, Gold in Vault (g), Silver in Vault (g), Total Principal Disbursed (₹), Total Collected (₹).
- **Date Filters**:
  - Filter by Date Range (`From Date` - `To Date`), with 1-click shortcuts for `Today`, `This Month`, and `All Time`.
- **Multiple Export Formats**:
  1. **📄 PDF Register Report** (Formatted report with shop header, filter summary, and totals via ReportLab).
  2. **📊 Genuine Microsoft Excel (.xlsx)** (Pure Python OpenXML generator; works out of the box with zero third-party Excel dependencies).
  3. **📑 CSV Export** (UTF-8 with BOM for 1-click opening in any spreadsheet).
  4. **🖨️ Printable Day Book** (Opens directly in system print viewer).

---

### 5. Backup, Security & Performance Architecture
- **Offline & Scalable Database**:
  - Local SQLite database stored at `data/jewelry_mortgage.db`.
  - Configured with `PRAGMA journal_mode = WAL;` (Write-Ahead Logging) and `PRAGMA foreign_keys = ON;` for high-throughput reads and concurrent safety.
  - B-tree indexes on `(serial_letter, serial_no)`, `customer_id`, `pledge_date`, `status`, `name`, `aadhar`, and `phone` ensuring lightning-fast search over 100,000+ entries.
- **Image Optimization Engine**:
  - High-resolution camera photos are automatically scaled to max 800px and compressed via JPEG Lanczos optimization (typically 60-100 KB).
  - Automatically generates 140px fast-loading thumbnails for list and grid views (typically 10-15 KB).
  - Memory LRU caching prevents Tkinter UI stuttering and ensures 60fps scrolling.
- **One-Click Backup & Disaster Recovery**:
  - Creates a single timestamped ZIP archive containing the SQLite database and all image directories.
  - Safe restore with emergency rollback snapshots.
- **Audit Trail**:
  - Logs all actions (New Pledges, Updates, Releases, Deletions, Settings Changes) with timestamps.

---

## 📁 Project Structure

```
d:\tkinter_app\
├── main.py                     # Main application entry point & view navigator
├── config.py                   # Business rules, interest rates, serial specs, color themes
├── seed_and_test.py            # Comprehensive verification & test suite
├── database/
│   ├── __init__.py
│   ├── db.py                   # SQLite connection, WAL mode, schema migrations
│   └── models.py               # Data Access Objects (Settings, Customers, Pledges, Connections, Audits)
├── services/
│   ├── __init__.py
│   ├── image_service.py        # Image compression, optimization, thumbnailing, cache
│   ├── interest_service.py     # Interest engine (Gold 2%, Silver 3%, settlement calculator)
│   ├── serial_service.py       # Serial letter A-Z, 1-9999, book/entry calculation
│   ├── report_service.py       # PDF generation (ReportLab), pure Excel (.xlsx), CSV export
│   └── backup_service.py       # Full system backup & restore (.zip)
├── ui/
│   ├── __init__.py
│   ├── theme.py                # Modern Slate & Gold TTK styles and typography
│   ├── components/
│   │   ├── autocomplete.py     # Search-as-you-type customer lookup with photo
│   │   ├── photo_picker.py     # File browse & live webcam snapshot picker
│   │   ├── connection_tree.py  # Anti-fraud relationship tree cards
│   │   ├── stat_card.py        # Metric stat cards for dashboard
│   │   └── toast.py            # Non-blocking notification toasts
│   └── views/
│       ├── dashboard_view.py   # Overview, inventory metrics, quick actions
│       ├── new_entry_view.py   # Pledge creation form
│       ├── search_view.py      # Search, inspector, edit & delete modal
│       ├── release_view.py     # Jewel redemption & settlement receipt
│       ├── register_view.py    # Day book register, exports, print
│       ├── customers_view.py   # Customer directory & relationship viewer
│       └── settings_view.py    # Shop profile, PIN, backup/restore, audit logs
└── data/                       # Local data storage
    ├── jewelry_mortgage.db     # SQLite database
    ├── backups/                # Backup archives
    └── images/                 # Organized image folders (customers, id_proofs, jewels, connections, thumbnails)
```

---

## 🚀 Running the Application

To launch the desktop application:

```bash
python main.py
```

To run the verification test suite:

```bash
python seed_and_test.py
```

---

## 🔒 Security & Admin PIN

- The default Admin Security PIN is **`1234`**.
- It is required to delete pledges or restore backups.
- You can change the PIN at any time under **Settings & Backup**.
