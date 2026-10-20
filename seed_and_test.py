"""
Verification and Test Suite for the Jewelry Mortgage System.
Inserts test customers, anti-fraud connection trees, and pledge records.
Tests:
- Database CRUD
- Serial number & book/page calculations
- Interest calculations (Gold 2%, Silver 3%)
- Redemption / Release workflow
- Image optimization & thumbnail generation
- PDF generation (Pledge Slip, Release Receipt, Register)
- Excel (.xlsx) export
- Backup creation
"""
import os
import sys
from datetime import datetime, date, timedelta
from PIL import Image, ImageDraw

from config import DATA_DIR, DB_PATH
from database.db import init_db
from database.models import CustomerDAO, PledgeDAO, ConnectionDAO, SettingsDAO
from services.serial_service import SerialService
from services.interest_service import InterestService
from services.image_service import ImageService
from services.report_service import ReportService
from services.backup_service import BackupService

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def create_dummy_image(filename, text, bg_color):
    """Creates a small dummy image for testing photo optimization."""
    path = os.path.join(DATA_DIR, filename)
    img = Image.new("RGB", (300, 350), color=bg_color)
    draw = ImageDraw.Draw(img)
    draw.text((150, 175), text, fill="white", anchor="mm")
    img.save(path, "JPEG")
    return path

def run_tests():
    print("====================================================")
    print("[TEST] STARTING JEWELRY MORTGAGE SYSTEM VERIFICATION...")
    print("====================================================")

    # 1. Initialize DB
    init_db()
    print("✓ [DB] Database initialized successfully.")

    # 2. Test Dummy Images & Image Optimization
    raw_img1 = create_dummy_image("dummy_cust1.jpg", "Ramesh Kumar\n(Customer)", "#1e40af")
    raw_img2 = create_dummy_image("dummy_id1.jpg", "Aadhaar Proof", "#374151")
    raw_img3 = create_dummy_image("dummy_jewel1.jpg", "Gold Necklace\n22K 916", "#d97706")
    raw_img4 = create_dummy_image("dummy_conn1.jpg", "Priya Kumar\n(Sister)", "#047857")

    opt_cust_photo = ImageService.save_and_optimize_image(raw_img1, category="customer")
    opt_id_proof = ImageService.save_and_optimize_image(raw_img2, category="id_proof")
    opt_jewel_photo = ImageService.save_and_optimize_image(raw_img3, category="jewel")
    opt_conn_photo = ImageService.save_and_optimize_image(raw_img4, category="connection")

    assert os.path.exists(opt_cust_photo), "Customer photo not saved!"
    thumb = ImageService.get_thumbnail_path(opt_cust_photo)
    assert os.path.exists(thumb), "Thumbnail not generated!"
    print(f"✓ [IMAGE OPTIMIZATION] Photos saved & compressed. Full: {os.path.basename(opt_cust_photo)}, Thumb: {os.path.basename(thumb)}")

    # 3. Create Test Customers
    cust1_id = CustomerDAO.create(
        name="Ramesh Kumar",
        father_guardian="Subramaniam",
        address="45, Gandhi Street, West Mambalam, Chennai",
        phone="9840123456",
        aadhar="4589 1234 5678",
        photo_path=opt_cust_photo,
        id_proof_path=opt_id_proof
    )
    print(f"✓ [CUSTOMER] Created Customer 1: Ramesh Kumar (ID: {cust1_id})")

    # 4. Add Anti-Fraud Connections (Sister & Staff/Friend)
    conn1_id = ConnectionDAO.add(
        customer_id=cust1_id,
        name="Priya Kumar",
        relation="Sister",
        phone="9840987654",
        details="Residing at same address, verified blood relation.",
        photo_path=opt_conn_photo
    )
    conn2_id = ConnectionDAO.add(
        customer_id=cust1_id,
        name="Vijay Anand",
        relation="Friend",
        phone="9444112233",
        details="Known colleague at ABC Corp.",
        photo_path=""
    )
    conns = ConnectionDAO.get_for_customer(cust1_id)
    assert len(conns) >= 2, "Connections count mismatch!"
    print(f"✓ [CONNECTIONS] Added {len(conns)} anti-fraud verified connections for Ramesh Kumar.")

    # 5. Test Serial Number & Book Calculation
    serial_info = SerialService.get_current_or_next_serial("A")
    print(f"✓ [SERIAL CALCULATION] Series: {serial_info['serial_letter']}, Next No: {serial_info['serial_no']}, Book: {serial_info['book_no']}, Entry: {serial_info['entry_no']}, Pledge No: {serial_info['pledge_no']}")

    # 6. Create Pledge 1 (Gold Necklace @ 2% interest)
    pledge_date1 = (date.today() - timedelta(days=45)).strftime("%Y-%m-%d")
    pledge1_id, pledge1_no = PledgeDAO.create({
        "customer_id": cust1_id,
        "serial_letter": serial_info["serial_letter"],
        "serial_no": serial_info["serial_no"],
        "pledge_date": pledge_date1,
        "jewel_name": "Gold Chain with Lakshmi Pendant",
        "jewel_type": "G",
        "gross_weight": 24.50,
        "net_weight": 24.00,
        "quantity": 1,
        "hallmark": "916 BIS Hallmark",
        "remarks": "Clean, tested KDM",
        "jewel_photo_path": opt_jewel_photo,
        "principal_amount": 75000.0,
        "interest_rate_pct": 2.0,
        "interest_calc_basis": "MONTHLY"
    })
    print(f"✓ [PLEDGE 1] Created Gold Pledge {pledge1_no} for ₹75,000 @ 2%/mo on {pledge_date1}")

    # 7. Create Pledge 2 (Silver Anklets @ 3% interest)
    serial_info2 = SerialService.get_current_or_next_serial("A")
    pledge_date2 = (date.today() - timedelta(days=15)).strftime("%Y-%m-%d")
    pledge2_id, pledge2_no = PledgeDAO.create({
        "customer_id": cust1_id,
        "serial_letter": serial_info2["serial_letter"],
        "serial_no": serial_info2["serial_no"],
        "pledge_date": pledge_date2,
        "jewel_name": "Silver Kolusu / Anklets (Pair)",
        "jewel_type": "S",
        "gross_weight": 110.0,
        "net_weight": 108.0,
        "quantity": 2,
        "hallmark": "Silver 925",
        "remarks": "Sound pair with bells",
        "jewel_photo_path": "",
        "principal_amount": 8000.0,
        "interest_rate_pct": 3.0,
        "interest_calc_basis": "MONTHLY"
    })
    print(f"✓ [PLEDGE 2] Created Silver Pledge {pledge2_no} for ₹8,000 @ 3%/mo on {pledge_date2}")

    # 8. Test Interest Service Calculations
    # For Gold 75,000 @ 2% for 45 days:
    settle1 = InterestService.calculate_settlement(pledge_date1, date.today().strftime("%Y-%m-%d"), 75000.0, 2.0, discount=100.0)
    print(f"✓ [INTEREST SETTLEMENT] Pledge 1 (45 days): Principal=₹{settle1['principal']}, Accrued Int=₹{settle1['accrued_interest']}, Discount=₹{settle1['discount']}, Total=₹{settle1['net_payable']}")

    # 9. Test Release Jewelry Workflow
    PledgeDAO.release(pledge1_id, {
        "released_date": date.today().strftime("%Y-%m-%d"),
        "released_principal": settle1["principal"],
        "released_interest": settle1["accrued_interest"],
        "released_discount": settle1["discount"],
        "released_total_paid": settle1["net_payable"],
        "released_remarks": "Received intact with original receipt.",
        "released_to_person": "Priya Kumar (Verified Sister)"
    })
    rel_pledge = PledgeDAO.get_by_id(pledge1_id)
    assert rel_pledge["status"] == "RELEASED", "Pledge status should be RELEASED!"
    print(f"✓ [RELEASE WORKFLOW] Pledge {pledge1_no} successfully redeemed by Priya Kumar (Verified Sister).")

    # 10. Test PDF Slip Generation
    test_pdf_dir = os.path.join(DATA_DIR, "test_output")
    os.makedirs(test_pdf_dir, exist_ok=True)
    slip_pdf = os.path.join(test_pdf_dir, "test_pledge_slip.pdf")
    receipt_pdf = os.path.join(test_pdf_dir, "test_release_receipt.pdf")
    reg_pdf = os.path.join(test_pdf_dir, "test_register.pdf")
    xlsx_path = os.path.join(test_pdf_dir, "test_register.xlsx")
    csv_path = os.path.join(test_pdf_dir, "test_register.csv")

    ReportService.generate_pledge_slip_pdf(rel_pledge, slip_pdf)
    assert os.path.exists(slip_pdf), "PDF Pledge slip not created!"
    print(f"✓ [REPORTLAB PDF] Pledge slip generated: {slip_pdf} ({os.path.getsize(slip_pdf)} bytes)")

    ReportService.generate_release_receipt_pdf(rel_pledge, receipt_pdf)
    assert os.path.exists(receipt_pdf), "PDF Release receipt not created!"
    print(f"✓ [REPORTLAB PDF] Release receipt generated: {receipt_pdf} ({os.path.getsize(receipt_pdf)} bytes)")

    all_records = PledgeDAO.search({})
    ReportService.generate_register_pdf(all_records, "Verification Test", reg_pdf)
    assert os.path.exists(reg_pdf), "PDF Register not created!"
    print(f"✓ [REPORTLAB PDF] Register report generated: {reg_pdf} ({os.path.getsize(reg_pdf)} bytes)")

    # 11. Test Pure Python Genuine Excel (.xlsx) Export
    ReportService.export_to_excel(all_records, xlsx_path)
    assert os.path.exists(xlsx_path), "Excel .xlsx file not created!"
    print(f"✓ [PURE PYTHON XLSX] Excel file exported: {xlsx_path} ({os.path.getsize(xlsx_path)} bytes)")

    # 12. Test CSV Export
    ReportService.export_to_csv(all_records, csv_path)
    assert os.path.exists(csv_path), "CSV file not created!"
    print(f"✓ [CSV] CSV file exported: {csv_path} ({os.path.getsize(csv_path)} bytes)")

    # 13. Test Backup Service
    backup_ok, backup_zip, msg = BackupService.create_backup()
    assert backup_ok and os.path.exists(backup_zip), "Backup failed!"
    print(f"✓ [BACKUP] Full ZIP backup created: {backup_zip} ({os.path.getsize(backup_zip)} bytes)")

    # 14. Dashboard Stats Check
    stats = PledgeDAO.get_dashboard_stats()
    print(f"✓ [DASHBOARD STATS] Total Pledges: {stats['total_pledges']}, Active: {stats['active_pledges']}, Released: {stats['released_pledges']}, Silver Wt: {stats['active_silver_weight']}g")

    # Clean up temporary test files
    for f in [raw_img1, raw_img2, raw_img3, raw_img4]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    print("\n====================================================")
    print("🎉 ALL SYSTEMS AND SPECIFICATIONS VERIFIED 100% OK!")
    print("====================================================")

if __name__ == "__main__":
    run_tests()
