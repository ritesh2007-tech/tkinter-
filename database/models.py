"""
Data Access Layer (DAO) for Customers, Connections, Pledges, Settings, and Audit Logs.
"""
import json
import math
import os
import sys
from datetime import datetime

if __package__ in (None, ""):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from database.db import get_connection

class SettingsDAO:
    @staticmethod
    def get(key, default=None):
        conn = get_connection()
        try:
            row = conn.execute("SELECT value FROM settings WHERE key = ?;", (key,)).fetchone()
            return row["value"] if row else default
        finally:
            conn.close()

    @staticmethod
    def set(key, value):
        conn = get_connection()
        try:
            conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value;", (key, str(value)))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_all():
        conn = get_connection()
        try:
            rows = conn.execute("SELECT key, value FROM settings;").fetchall()
            return {r["key"]: r["value"] for r in rows}
        finally:
            conn.close()


class CustomerDAO:
    @staticmethod
    def create(name, father_guardian="", address="", phone="", aadhar="", photo_path="", id_proof_path=""):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (name, father_guardian, address, phone, aadhar, photo_path, id_proof_path)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (name.strip(), father_guardian.strip(), address.strip(), phone.strip(), aadhar.strip(), photo_path, id_proof_path))
            conn.commit()
            cust_id = cursor.lastrowid
            AuditDAO.log("CREATE_CUSTOMER", str(cust_id), f"Created customer: {name} (Phone: {phone})")
            return cust_id
        finally:
            conn.close()

    @staticmethod
    def update(customer_id, name, father_guardian="", address="", phone="", aadhar="", photo_path=None, id_proof_path=None):
        conn = get_connection()
        try:
            # Build dynamic update to preserve existing photos if not replaced
            fields = ["name = ?", "father_guardian = ?", "address = ?", "phone = ?", "aadhar = ?", "updated_at = datetime('now', 'localtime')"]
            params = [name.strip(), father_guardian.strip(), address.strip(), phone.strip(), aadhar.strip()]

            if photo_path is not None:
                fields.append("photo_path = ?")
                params.append(photo_path)
            if id_proof_path is not None:
                fields.append("id_proof_path = ?")
                params.append(id_proof_path)

            params.append(customer_id)
            sql = f"UPDATE customers SET {', '.join(fields)} WHERE id = ?;"
            conn.execute(sql, params)
            conn.commit()
            AuditDAO.log("UPDATE_CUSTOMER", str(customer_id), f"Updated customer: {name}")
            return True
        finally:
            conn.close()

    @staticmethod
    def get_by_id(customer_id):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_proof_photos(cust_or_raw):
        """Extracts list of proof photo paths from customer record or raw string."""
        if not cust_or_raw:
            return []
        if hasattr(cust_or_raw, "keys") and "id_proof_path" in cust_or_raw.keys():
            raw = cust_or_raw["id_proof_path"]
        else:
            raw = cust_or_raw
        if not raw:
            return []
        if isinstance(raw, (list, tuple)):
            paths = raw
        else:
            raw = str(raw).strip()
            if raw.startswith("[") and raw.endswith("]"):
                try:
                    paths = json.loads(raw)
                except json.JSONDecodeError:
                    paths = [raw]
            else:
                paths = [raw]
        return [path for path in paths if isinstance(path, str) and path and os.path.exists(path)]

    @staticmethod
    def encode_proof_photos(photo_list):
        """Encodes list of proof photo paths into persistent string for database."""
        clean = [path for path in photo_list if isinstance(path, str) and path]
        return json.dumps(clean)

    @staticmethod
    def search(query, limit=10):
        """Live search for autocomplete and search box across Name, Aadhaar, Phone."""
        conn = get_connection()
        try:
            term = f"%{query.strip()}%"
            rows = conn.execute("""
                SELECT * FROM customers 
                WHERE name LIKE ? OR phone LIKE ? OR aadhar LIKE ?
                ORDER BY id DESC LIMIT ?;
            """, (term, term, term, limit)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def delete(customer_id):
        conn = get_connection()
        try:
            # Check if there are active pledges
            active = conn.execute("SELECT COUNT(*) as cnt FROM pledges WHERE customer_id = ? AND status = 'ACTIVE';", (customer_id,)).fetchone()
            if active and active["cnt"] > 0:
                raise ValueError("Cannot delete customer with active unreleased pledges.")
            
            # Delete pledges and customer
            conn.execute("DELETE FROM pledges WHERE customer_id = ?;", (customer_id,))
            conn.execute("DELETE FROM connections WHERE customer_id = ?;", (customer_id,))
            conn.execute("DELETE FROM customers WHERE id = ?;", (customer_id,))
            conn.commit()
            AuditDAO.log("DELETE_CUSTOMER", str(customer_id), f"Deleted customer ID: {customer_id}")
            return True
        finally:
            conn.close()


class ConnectionDAO:
    @staticmethod
    def add(customer_id, name, relation, phone="", details="", photo_path=""):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO connections (customer_id, name, relation, phone, details, photo_path)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (customer_id, name.strip(), relation.strip(), phone.strip(), details.strip(), photo_path))
            conn.commit()
            conn_id = cursor.lastrowid
            AuditDAO.log("ADD_CONNECTION", str(conn_id), f"Added connection {name} ({relation}) for Customer {customer_id}")
            return conn_id
        finally:
            conn.close()

    @staticmethod
    def get_for_customer(customer_id):
        conn = get_connection()
        try:
            rows = conn.execute("""
                SELECT * FROM connections WHERE customer_id = ? ORDER BY id ASC;
            """, (customer_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def update(connection_id, name, relation, phone="", details="", photo_path=None):
        conn = get_connection()
        try:
            fields = ["name = ?", "relation = ?", "phone = ?", "details = ?"]
            params = [name.strip(), relation.strip(), phone.strip(), details.strip()]
            if photo_path is not None:
                fields.append("photo_path = ?")
                params.append(photo_path)
            params.append(connection_id)
            sql = f"UPDATE connections SET {', '.join(fields)} WHERE id = ?;"
            conn.execute(sql, params)
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def delete(connection_id):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM connections WHERE id = ?;", (connection_id,))
            conn.commit()
            return True
        finally:
            conn.close()


class PledgeDAO:
    @staticmethod
    def get_next_serial_info(serial_letter):
        """
        Computes next available serial number (1-9999), Book No (1-100), and Entry No (1-100)
        for the given serial letter.
        """
        conn = get_connection()
        try:
            row = conn.execute("""
                SELECT MAX(serial_no) as max_no FROM pledges WHERE serial_letter = ?;
            """, (serial_letter,)).fetchone()
            
            max_no = row["max_no"] if row and row["max_no"] is not None else 0
            next_no = max_no + 1
            if next_no > 9999:
                next_no = 9999 # Max reached for this letter
            
            # 1 letter has 100 books, each book has 100 entries:
            # serial_no 1 -> book 1, entry 1
            # serial_no 100 -> book 1, entry 100
            # serial_no 101 -> book 2, entry 1
            book_no = math.ceil(next_no / 100)
            entry_no = ((next_no - 1) % 100) + 1
            pledge_no = f"{serial_letter}-{next_no:04d}"

            return {
                "serial_letter": serial_letter,
                "serial_no": next_no,
                "book_no": book_no,
                "entry_no": entry_no,
                "pledge_no": pledge_no
            }
        finally:
            conn.close()

    @staticmethod
    def is_serial_taken(serial_letter, serial_no, exclude_pledge_id=None):
        conn = get_connection()
        try:
            if exclude_pledge_id:
                row = conn.execute("SELECT id FROM pledges WHERE serial_letter = ? AND serial_no = ? AND id != ?;",
                                   (serial_letter, serial_no, exclude_pledge_id)).fetchone()
            else:
                row = conn.execute("SELECT id FROM pledges WHERE serial_letter = ? AND serial_no = ?;",
                                   (serial_letter, serial_no)).fetchone()
            return row is not None
        finally:
            conn.close()

    @staticmethod
    def create(data):
        """Create a new pledge entry."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            serial_letter = data["serial_letter"].upper()
            serial_no = int(data["serial_no"])
            book_no = math.ceil(serial_no / 100)
            entry_no = ((serial_no - 1) % 100) + 1
            pledge_no = f"{serial_letter}-{serial_no:04d}"

            cursor.execute("""
                INSERT INTO pledges (
                    customer_id, serial_letter, serial_no, book_no, entry_no, pledge_no,
                    pledge_date, jewel_name, jewel_type, gross_weight, net_weight,
                    quantity, hallmark, remarks, jewel_photo_path,
                    principal_amount, interest_rate_pct, interest_calc_basis, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE');
            """, (
                data["customer_id"], serial_letter, serial_no, book_no, entry_no, pledge_no,
                data["pledge_date"], data["jewel_name"], data["jewel_type"],
                float(data["gross_weight"]), float(data["net_weight"]),
                int(data.get("quantity", 1)), data.get("hallmark", ""),
                data.get("remarks", ""), data.get("jewel_photo_path", ""),
                float(data["principal_amount"]), float(data["interest_rate_pct"]),
                data.get("interest_calc_basis", "MONTHLY")
            ))
            conn.commit()
            pledge_id = cursor.lastrowid
            AuditDAO.log("NEW_PLEDGE", pledge_no, f"Pledge created: ₹{data['principal_amount']} on {data['jewel_name']}")
            return pledge_id, pledge_no
        finally:
            conn.close()

    @staticmethod
    def update(pledge_id, data):
        """Update existing pledge details."""
        conn = get_connection()
        try:
            fields = [
                "pledge_date = ?", "jewel_name = ?", "jewel_type = ?",
                "gross_weight = ?", "net_weight = ?", "quantity = ?",
                "hallmark = ?", "remarks = ?", "principal_amount = ?",
                "interest_rate_pct = ?", "interest_calc_basis = ?",
                "updated_at = datetime('now', 'localtime')"
            ]
            params = [
                data["pledge_date"], data["jewel_name"], data["jewel_type"],
                float(data["gross_weight"]), float(data["net_weight"]),
                int(data.get("quantity", 1)), data.get("hallmark", ""),
                data.get("remarks", ""), float(data["principal_amount"]),
                float(data["interest_rate_pct"]), data.get("interest_calc_basis", "MONTHLY")
            ]

            if "jewel_photo_path" in data and data["jewel_photo_path"] is not None:
                fields.append("jewel_photo_path = ?")
                params.append(data["jewel_photo_path"])

            params.append(pledge_id)
            sql = f"UPDATE pledges SET {', '.join(fields)} WHERE id = ?;"
            conn.execute(sql, params)
            conn.commit()
            AuditDAO.log("UPDATE_PLEDGE", str(pledge_id), "Pledge information updated")
            return True
        finally:
            conn.close()

    @staticmethod
    def release(pledge_id, release_data):
        """Mark a pledge as released with settlement details."""
        conn = get_connection()
        try:
            conn.execute("""
                UPDATE pledges SET
                    status = 'RELEASED',
                    released_date = ?,
                    released_principal = ?,
                    released_interest = ?,
                    released_discount = ?,
                    released_total_paid = ?,
                    released_remarks = ?,
                    released_to_person = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?;
            """, (
                release_data["released_date"],
                float(release_data["released_principal"]),
                float(release_data["released_interest"]),
                float(release_data.get("released_discount", 0.0)),
                float(release_data["released_total_paid"]),
                release_data.get("released_remarks", ""),
                release_data.get("released_to_person", ""),
                pledge_id
            ))
            conn.commit()
            AuditDAO.log("RELEASE_PLEDGE", str(pledge_id), f"Pledge redeemed. Paid: ₹{release_data['released_total_paid']}")
            return True
        finally:
            conn.close()

    @staticmethod
    def delete(pledge_id):
        conn = get_connection()
        try:
            row = conn.execute("SELECT pledge_no FROM pledges WHERE id = ?;", (pledge_id,)).fetchone()
            pledge_no = row["pledge_no"] if row else str(pledge_id)
            conn.execute("DELETE FROM pledges WHERE id = ?;", (pledge_id,))
            conn.commit()
            AuditDAO.log("DELETE_PLEDGE", pledge_no, f"Deleted pledge record {pledge_no}")
            return True
        finally:
            conn.close()

    @staticmethod
    def get_by_id(pledge_id):
        conn = get_connection()
        try:
            row = conn.execute("""
                SELECT p.*, c.name as customer_name, c.father_guardian, c.address, c.phone, c.aadhar,
                       c.photo_path as customer_photo_path, c.id_proof_path
                FROM pledges p
                JOIN customers c ON p.customer_id = c.id
                WHERE p.id = ?;
            """, (pledge_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_by_pledge_no(pledge_no):
        conn = get_connection()
        try:
            row = conn.execute("""
                SELECT p.*, c.name as customer_name, c.father_guardian, c.address, c.phone, c.aadhar,
                       c.photo_path as customer_photo_path, c.id_proof_path
                FROM pledges p
                JOIN customers c ON p.customer_id = c.id
                WHERE LOWER(p.pledge_no) = LOWER(?);
            """, (pledge_no.strip(),)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def search(query_dict=None, limit=200):
        """
        Search & filter pledges with multiple criteria:
        - text: searches pledge_no, customer name, aadhar, phone, jewel_name
        - status: 'ALL', 'ACTIVE', 'RELEASED'
        - jewel_type: 'ALL', 'G', 'S'
        - serial_letter: 'ALL' or specific letter
        - from_date, to_date: 'YYYY-MM-DD'
        """
        conn = get_connection()
        try:
            clauses = ["1=1"]
            params = []

            if query_dict:
                text = query_dict.get("text", "").strip()
                if text:
                    clauses.append("""
                        (p.pledge_no LIKE ? OR c.name LIKE ? OR c.aadhar LIKE ? OR c.phone LIKE ? OR p.jewel_name LIKE ?)
                    """)
                    term = f"%{text}%"
                    params.extend([term, term, term, term, term])

                status = query_dict.get("status", "ALL")
                if status and status != "ALL":
                    clauses.append("p.status = ?")
                    params.append(status)

                jtype = query_dict.get("jewel_type", "ALL")
                if jtype and jtype != "ALL":
                    clauses.append("p.jewel_type = ?")
                    params.append(jtype)

                serial_letter = query_dict.get("serial_letter", "ALL")
                if serial_letter and serial_letter != "ALL":
                    clauses.append("p.serial_letter = ?")
                    params.append(serial_letter)

                from_date = query_dict.get("from_date", "").strip()
                if from_date:
                    clauses.append("p.pledge_date >= ?")
                    params.append(from_date)

                to_date = query_dict.get("to_date", "").strip()
                if to_date:
                    clauses.append("p.pledge_date <= ?")
                    params.append(to_date)

            sql = f"""
                SELECT p.*, c.name as customer_name, c.phone as customer_phone, c.aadhar as customer_aadhar,
                       c.photo_path as customer_photo_path
                FROM pledges p
                JOIN customers c ON p.customer_id = c.id
                WHERE {' AND '.join(clauses)}
                ORDER BY p.id DESC LIMIT ?;
            """
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_dashboard_stats():
        conn = get_connection()
        try:
            stats = {}
            # Total pledges
            r = conn.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(principal_amount), 0) as total_amt FROM pledges;").fetchone()
            stats["total_pledges"] = r["cnt"]
            stats["total_amount_disbursed"] = r["total_amt"]

            # Active pledges
            r = conn.execute("""
                SELECT COUNT(*) as cnt, COALESCE(SUM(principal_amount), 0) as total_amt,
                       COALESCE(SUM(CASE WHEN jewel_type = 'G' THEN net_weight ELSE 0 END), 0) as gold_weight,
                       COALESCE(SUM(CASE WHEN jewel_type = 'S' THEN net_weight ELSE 0 END), 0) as silver_weight
                FROM pledges WHERE status = 'ACTIVE';
            """).fetchone()
            stats["active_pledges"] = r["cnt"]
            stats["active_amount"] = r["total_amt"]
            stats["active_gold_weight"] = r["gold_weight"]
            stats["active_silver_weight"] = r["silver_weight"]

            # Released pledges
            r = conn.execute("""
                SELECT COUNT(*) as cnt, COALESCE(SUM(released_total_paid), 0) as total_collected,
                       COALESCE(SUM(released_interest), 0) as total_interest_earned
                FROM pledges WHERE status = 'RELEASED';
            """).fetchone()
            stats["released_pledges"] = r["cnt"]
            stats["released_collected"] = r["total_collected"]
            stats["total_interest_earned"] = r["total_interest_earned"]

            # Total Customers
            r = conn.execute("SELECT COUNT(*) as cnt FROM customers;").fetchone()
            stats["total_customers"] = r["cnt"]

            return stats
        finally:
            conn.close()


class AuditDAO:
    @staticmethod
    def log(action_type, reference_id, details):
        conn = get_connection()
        try:
            conn.execute("""
                INSERT INTO audit_logs (action_type, reference_id, details)
                VALUES (?, ?, ?);
            """, (action_type, str(reference_id), details))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_recent(limit=50):
        conn = get_connection()
        try:
            rows = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?;", (limit,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
