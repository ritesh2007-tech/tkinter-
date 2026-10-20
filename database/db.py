"""
Database connection, initialization, and migration management.
Uses SQLite with WAL mode, foreign keys, and indexes for high scalability and offline performance.
"""
import sqlite3
import os
from config import DB_PATH, DEFAULT_ADMIN_PIN, DEFAULT_GOLD_RATE_PCT, DEFAULT_SILVER_RATE_PCT

def get_connection():
    """Get a SQLite database connection with row factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def init_db():
    """Initialize database tables, indexes, and default settings if not existing."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)

    # 2. Customers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        father_guardian TEXT,
        address TEXT,
        phone TEXT,
        aadhar TEXT,
        photo_path TEXT,
        id_proof_path TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        updated_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # 3. Connections Table (for fraud prevention, relationship tree, verified proof)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        relation TEXT NOT NULL,
        phone TEXT,
        details TEXT,
        photo_path TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );
    """)

    # 4. Pledges Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pledges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        serial_letter TEXT NOT NULL,
        serial_no INTEGER NOT NULL,
        book_no INTEGER NOT NULL,
        entry_no INTEGER NOT NULL,
        pledge_no TEXT NOT NULL UNIQUE,
        pledge_date TEXT NOT NULL,
        jewel_name TEXT NOT NULL,
        jewel_type TEXT NOT NULL,
        gross_weight REAL NOT NULL,
        net_weight REAL NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        hallmark TEXT,
        remarks TEXT,
        jewel_photo_path TEXT,
        principal_amount REAL NOT NULL,
        interest_rate_pct REAL NOT NULL,
        interest_calc_basis TEXT DEFAULT 'MONTHLY',
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        released_date TEXT,
        released_principal REAL,
        released_interest REAL,
        released_discount REAL DEFAULT 0.0,
        released_total_paid REAL,
        released_remarks TEXT,
        released_to_person TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        updated_at TEXT DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    );
    """)

    # 5. Audit Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        reference_id TEXT,
        details TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # 6. Optimized Indexes for lightning-fast queries over thousands of entries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pledges_serial ON pledges(serial_letter, serial_no);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pledges_customer ON pledges(customer_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pledges_date ON pledges(pledge_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pledges_status ON pledges(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_aadhar ON customers(aadhar);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_customer ON connections(customer_id);")

    # Insert default settings if missing
    defaults = {
        "shop_name": "SWARNA RATNA JEWEL MORTGAGE BANKERS",
        "shop_address": "108, Bazaar Main Road, Gold Market Complex",
        "shop_phone": "+91 98765 43210 / 044-24567890",
        "shop_license": "PAWN/LIC/2026/G-8872",
        "shop_gstin": "33AAAAA0000A1Z5",
        "gold_rate_pct": str(DEFAULT_GOLD_RATE_PCT),
        "silver_rate_pct": str(DEFAULT_SILVER_RATE_PCT),
        "admin_pin": DEFAULT_ADMIN_PIN,
        "current_serial_letter": "A",
    }

    for key, val in defaults.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", (key, val))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
