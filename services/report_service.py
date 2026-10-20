"""
Comprehensive Reporting and Export Service.
Generates:
- Professional PDF Pledge Slips / Pawn Vouchers (ReportLab)
- Professional PDF Release Receipts (ReportLab)
- PDF Day Book & Pledge Register (ReportLab)
- Genuine Excel (.xlsx) Spreadsheets (Pure Python via ZipFile & XML templates - zero dependencies!)
- CSV Exports (UTF-8 with BOM)
"""
import os
import csv
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from database.models import SettingsDAO

class ReportService:

    # -------------------------------------------------------------
    # 1. PDF PLEDGE SLIP / VOUCHER
    # -------------------------------------------------------------
    @classmethod
    def generate_pledge_slip_pdf(cls, pledge_data, output_path):
        """Generates a professional Pawn/Mortgage Pledge Slip with photos, details, terms, and signatures."""
        settings = SettingsDAO.get_all()
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        elements = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'ShopTitle',
            parent=styles['Heading1'],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#0f172a'),
            alignment=1, # Center
            fontName='Helvetica-Bold'
        )
        subtitle_style = ParagraphStyle(
            'ShopSubtitle',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#475569'),
            alignment=1
        )
        voucher_badge = ParagraphStyle(
            'Badge',
            parent=styles['Heading2'],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor('#b45309'),
            alignment=1,
            fontName='Helvetica-Bold'
        )
        label_style = ParagraphStyle('Label', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#1e293b'))
        val_style = ParagraphStyle('Val', parent=styles['Normal'], fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#0f172a'))
        terms_style = ParagraphStyle('Terms', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor('#64748b'))

        # Header Section
        shop_name = settings.get("shop_name", "SWARNA RATNA JEWEL MORTGAGE BANKERS")
        shop_addr = settings.get("shop_address", "108, Bazaar Main Road, Gold Market Complex")
        shop_phone = settings.get("shop_phone", "+91 98765 43210")
        shop_lic = settings.get("shop_license", "PAWN/LIC/2026/G-8872")

        elements.append(Paragraph(shop_name.upper(), title_style))
        elements.append(Paragraph(f"{shop_addr} | Phone: {shop_phone}", subtitle_style))
        elements.append(Paragraph(f"Govt. License No: {shop_lic} | Form No. F (Pawn Ticket)", subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#d97706'), spaceBefore=2, spaceAfter=8))

        # Pledge Title & Date Table
        meta_table_data = [
            [
                Paragraph(f"<b>PLEDGE NO:</b> <font color='#b45309' size=11><b>{pledge_data.get('pledge_no', '')}</b></font>", label_style),
                Paragraph(f"<b>Book No:</b> {pledge_data.get('book_no', '')} | <b>Entry No:</b> {pledge_data.get('entry_no', '')}", label_style),
                Paragraph(f"<b>Date:</b> {pledge_data.get('pledge_date', '')}", label_style)
            ]
        ]
        meta_table = Table(meta_table_data, colWidths=[200, 180, 150])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef3c7')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#f59e0b')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 10))

        # Customer Details & Photo Section
        cust_photo_path = pledge_data.get("customer_photo_path")
        photo_flowable = None
        if cust_photo_path and os.path.exists(cust_photo_path):
            try:
                photo_flowable = RLImage(cust_photo_path, width=1.1*inch, height=1.3*inch)
            except Exception:
                photo_flowable = Paragraph("[Photo]", label_style)
        else:
            photo_flowable = Paragraph("[No Photo]", label_style)

        cust_info_data = [
            [Paragraph("<b>Customer Name:</b>", label_style), Paragraph(str(pledge_data.get("customer_name", "")), val_style), photo_flowable],
            [Paragraph("<b>Father / Guardian / Spouse:</b>", label_style), Paragraph(str(pledge_data.get("father_guardian", "N/A")), val_style), ""],
            [Paragraph("<b>Phone Number:</b>", label_style), Paragraph(str(pledge_data.get("phone", "N/A")), val_style), ""],
            [Paragraph("<b>Aadhaar / ID No:</b>", label_style), Paragraph(str(pledge_data.get("aadhar", "N/A")), val_style), ""],
            [Paragraph("<b>Residential Address:</b>", label_style), Paragraph(str(pledge_data.get("address", "N/A")), val_style), ""]
        ]
        cust_table = Table(cust_info_data, colWidths=[150, 280, 100])
        cust_table.setStyle(TableStyle([
            ('SPAN', (2, 0), (2, 4)),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (2, 0), (2, 4), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(cust_table)
        elements.append(Spacer(1, 10))

        # Jewelry & Loan Details Table
        jtype_str = "Gold (G)" if pledge_data.get("jewel_type") == "G" else ("Silver (S)" if pledge_data.get("jewel_type") == "S" else "Other")
        principal = float(pledge_data.get("principal_amount", 0.0))
        rate_pct = float(pledge_data.get("interest_rate_pct", 2.0))
        monthly_interest = round(principal * (rate_pct / 100.0), 2)

        j_data = [
            [Paragraph("<b>Jewel Description</b>", label_style), Paragraph(str(pledge_data.get("jewel_name", "")), val_style)],
            [Paragraph("<b>Jewel Type</b>", label_style), Paragraph(jtype_str, val_style)],
            [Paragraph("<b>Gross Weight / Net Weight</b>", label_style), Paragraph(f"Gross: {pledge_data.get('gross_weight', 0)} g  |  <b>Net Wt: {pledge_data.get('net_weight', 0)} g</b>", val_style)],
            [Paragraph("<b>Quantity / Pieces</b>", label_style), Paragraph(f"{pledge_data.get('quantity', 1)} piece(s)", val_style)],
            [Paragraph("<b>Purity / Hallmark</b>", label_style), Paragraph(str(pledge_data.get("hallmark", "Not specified")), val_style)],
            [Paragraph("<b>Item Remarks / Condition</b>", label_style), Paragraph(str(pledge_data.get("remarks", "Clean, verified")), val_style)],
            [Paragraph("<b>Principal Loan Cash Given</b>", label_style), Paragraph(f"<font size=11 color='#16a34a'><b>₹ {principal:,.2f}</b></font>", val_style)],
            [Paragraph("<b>Interest Rate (% per month)</b>", label_style), Paragraph(f"<b>{rate_pct}% / month</b> (Gold 2%, Silver 3% standard)", val_style)],
            [Paragraph("<b>Monthly Interest Amount</b>", label_style), Paragraph(f"<b>₹ {monthly_interest:,.2f} / month</b>", val_style)],
        ]
        jewel_table = Table(j_data, colWidths=[180, 350])
        jewel_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(jewel_table)
        elements.append(Spacer(1, 10))

        # Terms and Conditions
        terms_text = (
            "<b>Terms & Conditions:</b> 1. Interest is payable monthly. 2. The borrower must produce this original ticket "
            "at the time of redemption. 3. Registered connection persons with valid photo proof will be verified before release. "
            "4. Articles not redeemed within 12 months from the date hereof are liable to be disposed of as per Pawnbrokers Act. "
            "5. The firm is not responsible for loss due to fire, robbery, or unforeseen natural disasters."
        )
        elements.append(Paragraph(terms_text, terms_style))
        elements.append(Spacer(1, 25))

        # Signatures
        sig_data = [
            [
                Paragraph("__________________________<br/><b>Customer / Pledger Signature</b>", label_style),
                Paragraph("__________________________<br/><b>Verified Connection / Guarantor</b>", label_style),
                Paragraph("__________________________<br/><b>For SWARNA RATNA BANKERS</b><br/>(Authorized Signatory)", label_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[175, 175, 180])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ]))
        elements.append(sig_table)

        doc.build(elements)
        return output_path

    # -------------------------------------------------------------
    # 2. PDF RELEASE RECEIPT
    # -------------------------------------------------------------
    @classmethod
    def generate_release_receipt_pdf(cls, pledge_data, output_path):
        """Generates a redemption / release voucher upon jewel delivery."""
        settings = SettingsDAO.get_all()
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=35,
            leftMargin=35,
            topMargin=35,
            bottomMargin=35
        )
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('ShopTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0f172a'), alignment=1, fontName='Helvetica-Bold')
        subtitle_style = ParagraphStyle('ShopSubtitle', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#475569'), alignment=1)
        label_style = ParagraphStyle('Label', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#1e293b'))
        val_style = ParagraphStyle('Val', parent=styles['Normal'], fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#0f172a'))

        shop_name = settings.get("shop_name", "SWARNA RATNA JEWEL MORTGAGE BANKERS")
        shop_addr = settings.get("shop_address", "108, Bazaar Main Road, Gold Market Complex")
        shop_phone = settings.get("shop_phone", "+91 98765 43210")

        elements.append(Paragraph(shop_name.upper(), title_style))
        elements.append(Paragraph(f"{shop_addr} | Phone: {shop_phone}", subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#16a34a'), spaceBefore=2, spaceAfter=8))

        badge = Paragraph("<b>JEWEL REDEMPTION / RELEASE RECEIPT</b>", ParagraphStyle('Bdg', parent=styles['Heading2'], alignment=1, textColor=colors.HexColor('#15803d')))
        elements.append(badge)
        elements.append(Spacer(1, 10))

        # Settlement details
        p_amt = float(pledge_data.get("released_principal", pledge_data.get("principal_amount", 0)))
        int_amt = float(pledge_data.get("released_interest", 0))
        disc_amt = float(pledge_data.get("released_discount", 0))
        tot_paid = float(pledge_data.get("released_total_paid", p_amt + int_amt - disc_amt))

        rel_data = [
            [Paragraph("<b>Pledge Number</b>", label_style), Paragraph(f"<b>{pledge_data.get('pledge_no', '')}</b>", val_style)],
            [Paragraph("<b>Customer Name</b>", label_style), Paragraph(str(pledge_data.get("customer_name", "")), val_style)],
            [Paragraph("<b>Pledge Date</b>", label_style), Paragraph(str(pledge_data.get("pledge_date", "")), val_style)],
            [Paragraph("<b>Release Date</b>", label_style), Paragraph(str(pledge_data.get("released_date", datetime.today().strftime('%Y-%m-%d'))), val_style)],
            [Paragraph("<b>Jewel Handed Over</b>", label_style), Paragraph(f"{pledge_data.get('jewel_name', '')} (Net Wt: {pledge_data.get('net_weight', 0)}g)", val_style)],
            [Paragraph("<b>Handed Over To Person</b>", label_style), Paragraph(str(pledge_data.get("released_to_person", pledge_data.get("customer_name", ""))), val_style)],
            [Paragraph("<b>Principal Repaid</b>", label_style), Paragraph(f"₹ {p_amt:,.2f}", val_style)],
            [Paragraph("<b>Interest Accrued</b>", label_style), Paragraph(f"₹ {int_amt:,.2f}", val_style)],
            [Paragraph("<b>Discount / Concession</b>", label_style), Paragraph(f"- ₹ {disc_amt:,.2f}", val_style)],
            [Paragraph("<b>Total Amount Received</b>", label_style), Paragraph(f"<font size=12 color='#15803d'><b>₹ {tot_paid:,.2f}</b></font>", val_style)],
            [Paragraph("<b>Remarks</b>", label_style), Paragraph(str(pledge_data.get("released_remarks", "Pledged jewelry received in intact sound condition.")), val_style)],
        ]
        table = Table(rel_data, colWidths=[180, 340])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#16a34a')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0fdf4')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        decl_text = "I hereby declare that I have received all the pledged jewelry items mentioned above in intact, good condition and full satisfaction, with no claims remaining."
        elements.append(Paragraph(f"<i>{decl_text}</i>", val_style))
        elements.append(Spacer(1, 35))

        sig_data = [
            [
                Paragraph("__________________________<br/><b>Receiver Signature & Date</b>", label_style),
                Paragraph("__________________________<br/><b>Authorized Cashier / Manager</b>", label_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[260, 260])
        sig_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
        elements.append(sig_table)

        doc.build(elements)
        return output_path

    # -------------------------------------------------------------
    # 3. PDF REGISTER / DAY BOOK
    # -------------------------------------------------------------
    @classmethod
    def generate_register_pdf(cls, records, filter_summary, output_path):
        """Generates formatted Day Book / Pledge Register PDF."""
        settings = SettingsDAO.get_all()
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=25,
            leftMargin=25,
            topMargin=25,
            bottomMargin=25
        )
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('RptTitle', parent=styles['Heading2'], fontSize=14, leading=16, alignment=1, fontName='Helvetica-Bold')
        sub_style = ParagraphStyle('RptSub', parent=styles['Normal'], fontSize=8.5, alignment=1, textColor=colors.HexColor('#475569'))
        cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=7.5, leading=9)
        head_style = ParagraphStyle('HCell', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.white)

        shop_name = settings.get("shop_name", "SWARNA RATNA JEWEL MORTGAGE BANKERS")
        elements.append(Paragraph(shop_name.upper(), title_style))
        elements.append(Paragraph(f"MORTGAGE REGISTER REPORT | Filter: {filter_summary} | Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", sub_style))
        elements.append(Spacer(1, 10))

        # Table Headers
        table_data = [[
            Paragraph("Pledge No", head_style),
            Paragraph("Date", head_style),
            Paragraph("Customer Name", head_style),
            Paragraph("Phone", head_style),
            Paragraph("Jewel Name", head_style),
            Paragraph("Type", head_style),
            Paragraph("Net Wt (g)", head_style),
            Paragraph("Principal (₹)", head_style),
            Paragraph("Status", head_style),
        ]]

        tot_principal = 0.0
        tot_gold_wt = 0.0
        tot_silver_wt = 0.0

        for r in records:
            p_amt = float(r.get("principal_amount", 0.0))
            net_wt = float(r.get("net_weight", 0.0))
            jtype = r.get("jewel_type", "G")
            status = r.get("status", "ACTIVE")

            tot_principal += p_amt
            if jtype == "G":
                tot_gold_wt += net_wt
            elif jtype == "S":
                tot_silver_wt += net_wt

            table_data.append([
                Paragraph(str(r.get("pledge_no", "")), cell_style),
                Paragraph(str(r.get("pledge_date", "")), cell_style),
                Paragraph(str(r.get("customer_name", "")), cell_style),
                Paragraph(str(r.get("customer_phone", "")), cell_style),
                Paragraph(str(r.get("jewel_name", "")), cell_style),
                Paragraph(jtype, cell_style),
                Paragraph(f"{net_wt:.2f}", cell_style),
                Paragraph(f"₹{p_amt:,.2f}", cell_style),
                Paragraph(status, cell_style),
            ])

        # Summary Row
        bold_cell = ParagraphStyle('BCell', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold')
        table_data.append([
            Paragraph("<b>TOTALS</b>", bold_cell),
            "", "", "",
            Paragraph(f"Records: {len(records)}", bold_cell),
            "",
            Paragraph(f"G: {tot_gold_wt:.1f}g<br/>S: {tot_silver_wt:.1f}g", bold_cell),
            Paragraph(f"₹ {tot_principal:,.2f}", bold_cell),
            ""
        ])

        col_widths = [55, 55, 95, 60, 95, 30, 50, 65, 45]
        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8fafc')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fef3c7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(tbl)
        doc.build(elements)
        return output_path

    # -------------------------------------------------------------
    # 4. PURE-PYTHON GENUINE EXCEL (.XLSX) GENERATOR
    # -------------------------------------------------------------
    @classmethod
    def export_to_excel(cls, records, file_path):
        """
        Creates an authentic Microsoft Excel (.xlsx) file using Python's standard library
        zipfile and XML templates. Requires zero third-party packages, 100% portable.
        """
        headers = [
            "Pledge No", "Date", "Book No", "Entry No", "Customer Name", "Father/Husband",
            "Phone", "Aadhaar", "Jewel Name", "Jewel Type", "Gross Wt (g)", "Net Wt (g)",
            "Quantity", "Hallmark", "Principal (₹)", "Interest %", "Status",
            "Release Date", "Released Paid (₹)"
        ]

        # Convert records to rows of strings
        rows = []
        for r in records:
            row = [
                str(r.get("pledge_no", "")),
                str(r.get("pledge_date", "")),
                str(r.get("book_no", "")),
                str(r.get("entry_no", "")),
                str(r.get("customer_name", "")),
                str(r.get("father_guardian", "")),
                str(r.get("customer_phone", "")),
                str(r.get("customer_aadhar", "")),
                str(r.get("jewel_name", "")),
                str(r.get("jewel_type", "")),
                str(r.get("gross_weight", "")),
                str(r.get("net_weight", "")),
                str(r.get("quantity", "")),
                str(r.get("hallmark", "")),
                str(r.get("principal_amount", "")),
                str(r.get("interest_rate_pct", "")),
                str(r.get("status", "")),
                str(r.get("released_date", "") or ""),
                str(r.get("released_total_paid", "") or ""),
            ]
            rows.append(row)

        cls._write_xlsx_archive(headers, rows, file_path)
        return file_path

    @classmethod
    def _write_xlsx_archive(cls, headers, rows, file_path):
        """Builds valid OpenXML package."""
        def col_letter(col_idx):
            res = ""
            while col_idx > 0:
                col_idx, rem = divmod(col_idx - 1, 26)
                res = chr(65 + rem) + res
            return res

        # Generate sheet XML
        sheet_lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
            '<sheetData>'
        ]

        # Row 1: Headers
        sheet_lines.append('<row r="1">')
        for c_idx, h in enumerate(headers, start=1):
            cell_ref = f"{col_letter(c_idx)}1"
            safe_text = str(h).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            sheet_lines.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{safe_text}</t></is></c>')
        sheet_lines.append('</row>')

        # Data Rows
        for r_idx, row in enumerate(rows, start=2):
            sheet_lines.append(f'<row r="{r_idx}">')
            for c_idx, val in enumerate(row, start=1):
                cell_ref = f"{col_letter(c_idx)}{r_idx}"
                # Check if number
                try:
                    num_val = float(val)
                    if num_val.is_integer() and "." not in val:
                        num_str = str(int(num_val))
                    else:
                        num_str = str(num_val)
                    sheet_lines.append(f'<c r="{cell_ref}"><v>{num_str}</v></c>')
                except ValueError:
                    safe_text = str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    sheet_lines.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{safe_text}</t></is></c>')
            sheet_lines.append('</row>')

        sheet_lines.append('</sheetData>')
        sheet_lines.append('</worksheet>')
        sheet_xml = "".join(sheet_lines)

        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '</Types>'
        )

        root_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        )

        workbook_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Mortgage Register" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>'
        )

        wb_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>'
        )

        with zipfile.ZipFile(file_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml', content_types)
            z.writestr('_rels/.rels', root_rels)
            z.writestr('xl/workbook.xml', workbook_xml)
            z.writestr('xl/_rels/workbook.xml.rels', wb_rels)
            z.writestr('xl/worksheets/sheet1.xml', sheet_xml)

    # -------------------------------------------------------------
    # 5. CSV EXPORT
    # -------------------------------------------------------------
    @classmethod
    def export_to_csv(cls, records, file_path):
        """Exports records to CSV with UTF-8 BOM encoding for seamless Excel import."""
        headers = [
            "Pledge No", "Date", "Book No", "Entry No", "Customer Name", "Father/Husband",
            "Phone", "Aadhaar", "Jewel Name", "Jewel Type", "Gross Wt (g)", "Net Wt (g)",
            "Quantity", "Hallmark", "Principal (₹)", "Interest %", "Status",
            "Release Date", "Released Paid (₹)"
        ]
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in records:
                writer.writerow([
                    r.get("pledge_no", ""),
                    r.get("pledge_date", ""),
                    r.get("book_no", ""),
                    r.get("entry_no", ""),
                    r.get("customer_name", ""),
                    r.get("father_guardian", ""),
                    r.get("customer_phone", ""),
                    r.get("customer_aadhar", ""),
                    r.get("jewel_name", ""),
                    r.get("jewel_type", ""),
                    r.get("gross_weight", ""),
                    r.get("net_weight", ""),
                    r.get("quantity", ""),
                    r.get("hallmark", ""),
                    r.get("principal_amount", ""),
                    r.get("interest_rate_pct", ""),
                    r.get("status", ""),
                    r.get("released_date", "") or "",
                    r.get("released_total_paid", "") or ""
                ])
        return file_path
