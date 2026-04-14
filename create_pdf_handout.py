"""
Generate Project Sentinel PDF handout with:
- Presentation script (speaker notes)
- Project overview with architecture diagrams
- Validation results
- Feature inventory
- Security controls
- Roadmap
- Q&A cheat sheet
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image, KeepTogether
)
from reportlab.lib import colors

# ── Brand Colors ──
NAVY = HexColor("#1E3161")
NAVY_DARK = HexColor("#0B1929")
SAGE = HexColor("#DDE9E8")
GREEN = HexColor("#27AE60")
RED = HexColor("#E74C3C")
AMBER = HexColor("#F39C12")
TEXT_DARK = HexColor("#1E3161")
TEXT_LIGHT = HexColor("#5A6B7F")
BORDER = HexColor("#E0E0E0")
WHITE_BG = HexColor("#FFFFFF")
SAGE_BG = HexColor("#F0F5F4")

OUT_PATH = os.path.join(os.path.dirname(__file__), "Project_Sentinel_Handout.pdf")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "calibrium_logo.png")

# ── Styles ──
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    "CTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=28, textColor=NAVY, spaceAfter=6, alignment=TA_LEFT,
))
styles.add(ParagraphStyle(
    "CSubtitle", parent=styles["Normal"], fontName="Helvetica",
    fontSize=14, textColor=TEXT_LIGHT, spaceAfter=20, alignment=TA_LEFT,
))
styles.add(ParagraphStyle(
    "CH1", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=20, textColor=NAVY, spaceBefore=24, spaceAfter=10,
))
styles.add(ParagraphStyle(
    "CH2", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=15, textColor=NAVY, spaceBefore=16, spaceAfter=8,
))
styles.add(ParagraphStyle(
    "CH3", parent=styles["Heading3"], fontName="Helvetica-Bold",
    fontSize=12, textColor=TEXT_DARK, spaceBefore=10, spaceAfter=4,
))
styles.add(ParagraphStyle(
    "CBody", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10, textColor=TEXT_DARK, leading=14, spaceAfter=6,
    alignment=TA_JUSTIFY,
))
styles.add(ParagraphStyle(
    "CScript", parent=styles["Normal"], fontName="Helvetica-Oblique",
    fontSize=10, textColor=TEXT_LIGHT, leading=14, spaceAfter=8,
    leftIndent=12, alignment=TA_JUSTIFY,
))
styles.add(ParagraphStyle(
    "CStageDir", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=9, textColor=AMBER, spaceAfter=4,
))
styles.add(ParagraphStyle(
    "CQuestion", parent=styles["Normal"], fontName="Helvetica-BoldOblique",
    fontSize=11, textColor=NAVY, spaceBefore=12, spaceAfter=4,
))
styles.add(ParagraphStyle(
    "CAnswer", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10, textColor=TEXT_DARK, leading=14, spaceAfter=10,
    leftIndent=12, alignment=TA_JUSTIFY,
))
styles.add(ParagraphStyle(
    "CFooter", parent=styles["Normal"], fontName="Helvetica",
    fontSize=8, textColor=TEXT_LIGHT, alignment=TA_CENTER,
))

def make_header_line():
    return HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=12)

def make_thin_line():
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=8, spaceAfter=8)

def make_table(headers, rows, col_widths=None):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_DARK),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE_BG, SAGE_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t

# ── Page template with header/footer ──
def on_page(canvas, doc):
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(1.5)
    canvas.line(20*mm, A4[1] - 15*mm, A4[0] - 20*mm, A4[1] - 15*mm)
    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.drawString(20*mm, 12*mm, "Project Sentinel | Calibrium AG | Confidential")
    canvas.drawRightString(A4[0] - 20*mm, 12*mm, f"Page {doc.page}")
    canvas.restoreState()

def on_first_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, A4[1] - 90*mm, A4[0], 90*mm, fill=1)
    # Logo
    if os.path.exists(LOGO_PATH.replace("calibrium_logo", "calibrium_logo_white")):
        canvas.drawImage(LOGO_PATH.replace("calibrium_logo", "calibrium_logo_white"),
                         20*mm, A4[1] - 30*mm, width=50*mm, height=12*mm,
                         preserveAspectRatio=True, mask="auto")
    canvas.setFont("Helvetica-Bold", 32)
    canvas.setFillColor(white)
    canvas.drawString(20*mm, A4[1] - 52*mm, "Project Sentinel")
    canvas.setFont("Helvetica", 16)
    canvas.setFillColor(HexColor("#DDE9E8"))
    canvas.drawString(20*mm, A4[1] - 65*mm, "Treasury Operations Automation")
    canvas.setFont("Helvetica", 11)
    canvas.setFillColor(HexColor("#B0C4D8"))
    canvas.drawString(20*mm, A4[1] - 78*mm, "Private Equity Capital Call Processing  |  Calibrium AG  |  April 2026")
    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.drawString(20*mm, 12*mm, "Project Sentinel | Calibrium AG | Confidential")
    canvas.drawRightString(A4[0] - 20*mm, 12*mm, f"Page {doc.page}")
    canvas.restoreState()


# ══════════════════════════════════════
# BUILD THE DOCUMENT
# ══════════════════════════════════════
doc = SimpleDocTemplate(
    OUT_PATH, pagesize=A4,
    leftMargin=20*mm, rightMargin=20*mm,
    topMargin=22*mm, bottomMargin=20*mm,
)

story = []

# ── COVER PAGE ──
story.append(Spacer(1, 75*mm))  # Space for the navy header drawn on canvas
story.append(Paragraph("Presentation Handout & Project Overview", styles["CSubtitle"]))
story.append(Spacer(1, 8*mm))
story.append(Paragraph(
    "This document contains the complete presentation script with speaker notes, "
    "a technical overview of the Project Sentinel architecture, validation results, "
    "feature inventory, security controls, roadmap, and a Q&A reference guide.",
    styles["CBody"]
))
story.append(Spacer(1, 6*mm))

# Table of contents
toc_data = [
    ["Section", "Page"],
    ["1. Project Overview & Architecture", "2"],
    ["2. Validation Results", "3"],
    ["3. Feature Inventory", "3"],
    ["4. Security & Risk Controls", "4"],
    ["5. Roadmap & Future Outlook", "4"],
    ["6. Presentation Script (Slides 1-10)", "5"],
    ["7. Live Demo Flow", "8"],
    ["8. Q&A Cheat Sheet", "9"],
    ["9. Technical Specifications", "10"],
]
toc = Table(toc_data, colWidths=[130*mm, 25*mm])
toc.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 10),
    ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_DARK),
    ("LINEBELOW", (0, 0), (-1, 0), 1, NAVY),
    ("LINEBELOW", (0, 1), (-1, -1), 0.25, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(toc)
story.append(PageBreak())

# ══════════════════════════════════════
# SECTION 1: PROJECT OVERVIEW
# ══════════════════════════════════════
story.append(Paragraph("1. Project Overview & Architecture", styles["CH1"]))
story.append(make_header_line())

story.append(Paragraph(
    "Project Sentinel automates the end-to-end processing of Private Equity capital call notices. "
    "It replaces manual PDF-to-spreadsheet workflows with AI-driven extraction, automated risk "
    "validation, and a role-based approval system with full audit trail.",
    styles["CBody"]
))

story.append(Paragraph("Processing Pipeline", styles["CH2"]))
pipeline_data = [
    ["Step", "Component", "Description"],
    ["1. Upload", "Streamlit File Uploader", "Drag-and-drop single or batch (up to 20 PDFs)"],
    ["2. Extract", "Smart Extractor", "Regex parser (primary) + Claude API (fallback for complex PDFs)"],
    ["3. Match", "Fuzzy Matching Engine", "Fund name matching with Roman numeral normalization (rapidfuzz)"],
    ["4. Validate", "Validation Engine", "Commitment check + Wire verification + Duplicate detection"],
    ["5. Approve", "4-Eye Workflow", "Role-based (analyst/reviewer/admin), reviewer != submitter"],
    ["6. Execute", "Database Layer", "Atomic transaction: update commitment, log audit, generate email"],
    ["7. Report", "Audit & Export", "Searchable audit log, Excel export, PDF archive"],
]
story.append(make_table(pipeline_data[0], pipeline_data[1:], col_widths=[18*mm, 38*mm, 100*mm]))
story.append(Spacer(1, 4*mm))

story.append(Paragraph("Architecture Layers", styles["CH2"]))
arch_data = [
    ["Layer", "Technology", "Purpose"],
    ["Web UI", "Streamlit", "Dashboard, process, audit, wire management, portfolio tracking"],
    ["Extraction", "pdfplumber + Claude API", "Dual-mode PDF parsing, multi-language (EN/DE/FR/IT/ES)"],
    ["Validation", "rapidfuzz + custom logic", "Commitment check, IBAN verification, fuzzy matching"],
    ["Persistence", "SQLite (WAL mode)", "10 tables, atomic transactions, auto-seed from Excel"],
    ["Reporting", "Plotly + openpyxl", "Interactive charts, multi-sheet Excel export"],
]
story.append(make_table(arch_data[0], arch_data[1:], col_widths=[28*mm, 42*mm, 86*mm]))
story.append(Spacer(1, 4*mm))

story.append(Paragraph("Database Schema (10 Tables)", styles["CH2"]))
schema_data = [
    ["Table", "Purpose", "Key Fields"],
    ["commitment_tracker", "Mutable fund state", "investor, fund_name, total_commitment, remaining"],
    ["executed_calls", "Payment history (append-only)", "fund_name, amount, value_date, source"],
    ["processed_calls", "Full audit trail", "filename, validation_json, action, reviewer"],
    ["approved_wires", "Verified banking details", "fund_name, iban, swift_bic, beneficiary_bank"],
    ["wire_change_requests", "Wire update workflow", "field_changed, old/new_value, status"],
    ["commitment_amendments", "Commitment increase requests", "requested_increase, reason, status"],
    ["users", "Role-based access", "username, role (analyst/reviewer/admin)"],
    ["distributions", "Fund distributions", "amount, distribution_type, value_date"],
    ["nav_records", "Net Asset Value snapshots", "fund_name, nav_amount, reporting_date"],
    ["gp_contacts", "Counterparty directory", "contact_name, role, email, phone"],
]
story.append(make_table(schema_data[0], schema_data[1:], col_widths=[38*mm, 42*mm, 76*mm]))

story.append(PageBreak())

# ══════════════════════════════════════
# SECTION 2: VALIDATION RESULTS
# ══════════════════════════════════════
story.append(Paragraph("2. Validation Results", styles["CH1"]))
story.append(make_header_line())

story.append(Paragraph(
    "The system was tested against 4 capital call notices with deliberately planted validation traps. "
    "The engine correctly identified 2 rejections and 2 approvals:",
    styles["CBody"]
))

val_headers = ["Notice", "Fund", "Amount", "Commitment", "Wire", "Result"]
val_rows = [
    ["Notice 1", "GT Partners IV Equity", "EUR 5.6M", "FAIL", "PASS", "REJECTED"],
    ["Notice 2", "GT Partners V Equity", "EUR 6.0M", "PASS", "FAIL", "REJECTED"],
    ["Notice 3", "Parallax Buyout II", "EUR 9.3M", "PASS", "PASS", "APPROVED"],
    ["Notice 4", "GT Partners VI Equity", "EUR 4.8M", "PASS", "PASS", "APPROVED"],
]
val_table = make_table(val_headers, val_rows, col_widths=[20*mm, 38*mm, 22*mm, 25*mm, 18*mm, 25*mm])
# Color-code PASS/FAIL cells
for i, row in enumerate(val_rows):
    r = i + 1
    for j, cell in enumerate(row):
        if cell == "FAIL":
            val_table.setStyle(TableStyle([("TEXTCOLOR", (j, r), (j, r), RED), ("FONTNAME", (j, r), (j, r), "Helvetica-Bold")]))
        elif cell == "PASS":
            val_table.setStyle(TableStyle([("TEXTCOLOR", (j, r), (j, r), GREEN), ("FONTNAME", (j, r), (j, r), "Helvetica-Bold")]))
        elif cell == "REJECTED":
            val_table.setStyle(TableStyle([("BACKGROUND", (j, r), (j, r), HexColor("#FDEDEE")), ("TEXTCOLOR", (j, r), (j, r), RED), ("FONTNAME", (j, r), (j, r), "Helvetica-Bold")]))
        elif cell == "APPROVED":
            val_table.setStyle(TableStyle([("BACKGROUND", (j, r), (j, r), HexColor("#E8F8EF")), ("TEXTCOLOR", (j, r), (j, r), GREEN), ("FONTNAME", (j, r), (j, r), "Helvetica-Bold")]))
story.append(val_table)
story.append(Spacer(1, 4*mm))

story.append(Paragraph("Key Findings", styles["CH2"]))
story.append(Paragraph(
    "<b>Notice 1 (Over-Commitment):</b> EUR 5.6M requested against EUR 3.9M remaining. "
    "System blocks execution and offers a commitment amendment workflow.",
    styles["CBody"]
))
story.append(Paragraph(
    "<b>Notice 2 (Wire Fraud Signal):</b> PDF shows German IBAN (DE89...) but approved records show "
    "Swiss IBAN (CH12...). Different country, different bank. System flags as potential fraud "
    "and displays GP contact for immediate escalation.",
    styles["CBody"]
))
story.append(Paragraph(
    "<b>Notice 4 (Fuzzy Matching):</b> PDF uses digit \"6\" while database has Roman numeral \"VI\". "
    "The normalization engine converts both to the same form, achieving 100% match confidence.",
    styles["CBody"]
))

# ══════════════════════════════════════
# SECTION 3: FEATURE INVENTORY
# ══════════════════════════════════════
story.append(Paragraph("3. Feature Inventory (15 Features Delivered)", styles["CH1"]))
story.append(make_header_line())

feat_data = [
    ["#", "Feature", "Category", "Description"],
    ["1", "AI Extraction", "Core", "Regex + Claude API dual-mode PDF parsing"],
    ["2", "Commitment Check", "Validation", "Amount vs remaining open commitment"],
    ["3", "Wire Verification", "Validation", "IBAN normalization + approved wire matching"],
    ["4", "4-Eye Approval", "Workflow", "Role-based, reviewer != submitter, 2-step confirm"],
    ["5", "Batch Upload", "Efficiency", "Process up to 20 PDFs with summary table"],
    ["6", "Due Date Alerts", "Monitoring", "Color-coded urgency badges + countdown"],
    ["7", "Cash Position", "Dashboard", "Pending outflow forecasting by date/investor"],
    ["8", "PDF Preview", "UX", "Side-by-side original PDF and extracted data"],
    ["9", "Wire Change Mgmt", "Compliance", "Dual-auth workflow for banking detail updates"],
    ["10", "Commitment Amend", "Workflow", "Formal increase request with approval chain"],
    ["11", "Multi-Language", "Extraction", "EN, DE, FR, IT, ES regex patterns"],
    ["12", "Duplicate Detection", "Validation", "Exact + fuzzy match with override"],
    ["13", "Portfolio Summary", "Analytics", "TVPI/DPI metrics, cumulative cash flows"],
    ["14", "Excel Export", "Reporting", "Multi-sheet workbook with formatted data"],
    ["15", "Dark/Light Mode", "UX", "Full theme support across all components"],
]
story.append(make_table(feat_data[0], feat_data[1:], col_widths=[10*mm, 35*mm, 25*mm, 86*mm]))

story.append(PageBreak())

# ══════════════════════════════════════
# SECTION 4: SECURITY
# ══════════════════════════════════════
story.append(Paragraph("4. Security & Risk Controls", styles["CH1"]))
story.append(make_header_line())

sec_data = [
    ["Control", "Type", "Description"],
    ["Commitment Check", "Automated", "Validates amount against remaining open commitment"],
    ["Wire Verification", "Automated", "IBAN normalized and compared to approved database"],
    ["Duplicate Detection", "Automated", "Exact + fuzzy matching prevents re-processing"],
    ["Zero-Amount Guard", "Automated", "Blocks approval when amount extraction fails"],
    ["4-Eye Principle", "Process", "Enforced at DB level: reviewer != submitter"],
    ["XSS Prevention", "Technical", "HTML-escaped PDF data in all rendered output"],
    ["Wire Change Audit", "Process", "Dual-authorization for banking detail modifications"],
    ["SMTP Isolation", "Technical", "Email passwords in session memory only, never in DB"],
]
story.append(make_table(sec_data[0], sec_data[1:], col_widths=[35*mm, 22*mm, 99*mm]))

# ══════════════════════════════════════
# SECTION 5: ROADMAP
# ══════════════════════════════════════
story.append(Spacer(1, 6*mm))
story.append(Paragraph("5. Roadmap & Future Outlook", styles["CH1"]))
story.append(make_header_line())

road_data = [
    ["Phase", "Feature", "Business Value"],
    ["Now", "OCR for scanned PDFs", "Handle image-based notices from legacy GPs"],
    ["Now", "Multi-currency + FX rates", "Process USD/GBP/CHF calls with conversion"],
    ["Now", "SMTP email sending", "Send confirmations directly from the app"],
    ["Next", "SSO / Azure AD authentication", "Replace dropdown with enterprise login"],
    ["Next", "Cash position forecasting", "Predict liquidity needs from schedules"],
    ["Next", "Slack/Teams notifications", "Alert on due dates and validation failures"],
    ["Next", "Regulatory audit PDF export", "Compliance-ready reports for auditors"],
    ["Future", "GP Portal API integration", "Electronic notices, eliminate PDF parsing"],
    ["Future", "ML anomaly detection", "Flag unusual call patterns proactively"],
    ["Future", "SWIFT MT103 generation", "Straight-through payment processing"],
    ["Future", "Mobile push approvals", "Approve on-the-go for reviewers"],
]
story.append(make_table(road_data[0], road_data[1:], col_widths=[20*mm, 48*mm, 88*mm]))

story.append(PageBreak())

# ══════════════════════════════════════
# SECTION 6: PRESENTATION SCRIPT
# ══════════════════════════════════════
story.append(Paragraph("6. Presentation Script", styles["CH1"]))
story.append(make_header_line())
story.append(Paragraph(
    "Duration: ~15-20 minutes (presentation) + 10 minutes (live demo) + Q&A",
    styles["CBody"]
))

slides = [
    ("Slide 1: Title", [
        ("script", "Good morning/afternoon everyone. Today I'm presenting Project Sentinel -- a Treasury Operations Automation tool we built to solve a very real problem in our Private Equity capital call processing."),
        ("script", "The goal was simple: take a manual, error-prone workflow and turn it into an automated, auditable, and fraud-resistant system."),
        ("stage", "[Pause, advance]"),
    ]),
    ("Slide 2: The Problem", [
        ("script", "Let me start with why we built this. Our treasury team faces four key challenges:"),
        ("script", "First -- Manual Processing. Every quarter we receive 10 to 20 capital call PDFs from different GPs. Today, someone manually opens each PDF, copies the fund name, amount, IBAN, and due date into a spreadsheet. That's slow, and it's where mistakes happen."),
        ("script", "Second -- No Systematic Validation. When a capital call comes in, we need to check: is the amount within our remaining commitment, and is the IBAN correct? Right now that's done ad-hoc."),
        ("script", "Third -- Format Chaos. Every GP sends notices differently. Some in English, some German, some French. Different layouts, different number formats."),
        ("script", "Fourth -- Audit Gaps. If a regulator asks 'who approved this EUR 5 million wire transfer?' -- today we'd struggle to answer cleanly."),
        ("stage", "[Pause, advance]"),
    ]),
    ("Slide 3: The Solution", [
        ("script", "Project Sentinel solves all four in a single platform. Five steps:"),
        ("script", "Upload -- drag and drop, single or batch. AI Extraction -- regex parser for structured PDFs, Claude API fallback for messy ones. Auto-Validate -- commitment check and wire verification run instantly. 4-Eye Approval -- a second person must confirm. Track and Report -- full audit trail, searchable, exportable."),
        ("stage", "[Pause, advance]"),
    ]),
    ("Slide 4: Validation Engine", [
        ("script", "We tested with four capital call notices. The system correctly identified two that should be rejected."),
        ("script", "Notice 1: EUR 5.6 million requested but only EUR 3.9 million remaining. Flagged immediately."),
        ("script", "Notice 2: The commitment check passes, but the wire verification catches a critical issue -- the IBAN is a German account number, while our records show a Swiss account. Potential fraud. Blocked immediately."),
        ("script", "Notice 4 is interesting: the PDF says 'GT Partners 6' with a digit, but our database has 'GT Partners VI' with Roman numerals. The fuzzy matching engine normalizes both and matches them correctly."),
        ("stage", "[If asked about failures: amendment workflow for commitment, GP contacts for wire escalation]"),
    ]),
    ("Slide 5: Key Features", [
        ("script", "Beyond the core workflow, we've built 12 additional features: batch upload, wire change management, commitment amendments, portfolio tracking with TVPI/DPI, multi-language support for 5 languages, duplicate detection, Excel export, and more."),
        ("stage", "[Highlight 3-4 most relevant to your audience]"),
    ]),
    ("Slide 6: Security & Risk Controls", [
        ("script", "Security was built in from day one. Eight controls: commitment check, wire verification, duplicate detection, 4-eye principle enforced at the database level, XSS prevention, zero-amount guard, wire change audit, and SMTP password isolation."),
        ("stage", "[If asked about compliance: technical controls are in place, formal certification would need procedural documentation]"),
    ]),
    ("Slide 7: Architecture", [
        ("script", "Simple, self-contained architecture. Streamlit for the UI, regex plus Claude API for extraction, custom validation engine, SQLite with WAL mode for persistence. Everything open-source except the optional Claude API. 50 automated tests covering every critical path."),
        ("stage", "[If asked about SQLite vs PostgreSQL: perfect for 5-10 users, migration is a config change]"),
    ]),
    ("Slide 8: Roadmap", [
        ("script", "Three phases. Now: OCR, multi-currency, SMTP sending. Next: SSO authentication, cash forecasting, notifications. Future: GP API integration, ML anomaly detection, SWIFT payment generation."),
        ("stage", "[Pause, advance]"),
    ]),
    ("Slide 9: By the Numbers", [
        ("script", "EUR 255 million in commitments tracked. 12 funds across 3 vintages. 34+ historical payments. 50 automated tests. 5 languages supported. 15 features delivered."),
        ("stage", "[Brief -- numbers speak for themselves]"),
    ]),
    ("Slide 10: Live Demo", [
        ("script", "Now let me show you the actual system."),
        ("stage", "[Switch to browser at http://localhost:8501]"),
    ]),
]

for title, items in slides:
    story.append(Paragraph(title, styles["CH2"]))
    for kind, text in items:
        if kind == "script":
            story.append(Paragraph(text, styles["CScript"]))
        elif kind == "stage":
            story.append(Paragraph(text, styles["CStageDir"]))
    story.append(make_thin_line())

story.append(PageBreak())

# ══════════════════════════════════════
# SECTION 7: LIVE DEMO FLOW
# ══════════════════════════════════════
story.append(Paragraph("7. Live Demo Flow (5-10 minutes)", styles["CH1"]))
story.append(make_header_line())

demo_steps = [
    ("1. Dashboard Overview (~1 min)", [
        "Show KPI cards: EUR 255M commitments, EUR 118M funded, EUR 137M remaining",
        "Point out the red due-date alert banner at the top",
        "Use the vintage filter to narrow to 'C - Fund Vintage 2015'",
        "Scroll to Cash Position section showing pending outflows",
    ]),
    ("2. Process a Good Notice (~2 min)", [
        "Upload Notice_3_Parallax_Buyout_II.pdf",
        "Show PDF preview on the left, extracted data on the right",
        "Point out: both checks PASS, 60.8% commitment utilization",
        "Select Anna Schmidt as reviewer, click Confirm & Execute",
        "Show the confirmation dialog, then approve",
        "Point out the email template generated below",
    ]),
    ("3. Process a Bad Notice (~2 min)", [
        "Upload Notice_2_GT_V_Equity.pdf",
        "Commitment check PASSES -- EUR 6M within EUR 12M remaining",
        "Wire verification FAILS -- IBAN mismatch flagged as fraud risk",
        "Show the GP contact card for immediate escalation",
    ]),
    ("4. Batch Upload (~1 min)", [
        "Upload all 4 PDFs at once",
        "Show the progress bar and summary table",
        "Point out: 2 approved, 2 rejected, with details per file",
    ]),
    ("5. Dark Mode (~10 sec)", [
        "Toggle dark mode switch in the sidebar",
        "Show full theme support across all components",
    ]),
    ("6. Audit Log (~30 sec)", [
        "Show all processed calls with status badges",
        "Demonstrate filters (by status, fund, reviewer)",
        "Click Download Excel button",
    ]),
]

for title, steps in demo_steps:
    story.append(Paragraph(title, styles["CH2"]))
    for step in steps:
        story.append(Paragraph(f"  {step}", styles["CBody"]))
    story.append(Spacer(1, 2*mm))

story.append(PageBreak())

# ══════════════════════════════════════
# SECTION 8: Q&A CHEAT SHEET
# ══════════════════════════════════════
story.append(Paragraph("8. Q&A Cheat Sheet", styles["CH1"]))
story.append(make_header_line())

qas = [
    ("How long did this take to build?",
     "The core system was built in one intensive sprint. The 15 additional features were developed in parallel across three waves using Claude Code's multi-session orchestration."),
    ("What happens if the PDF parser fails?",
     "Two fallbacks: first the Claude AI API attempts extraction, then the system shows a clear error and blocks processing. It never silently approves incomplete data."),
    ("Can we use this with real data?",
     "Yes. Delete sentinel.db, replace the Excel with your actual commitment tracker, and the system re-seeds on first launch."),
    ("What about compliance / audit requirements?",
     "Every action is logged with timestamp, user identity, validation results, and reviewer approval. The audit log is searchable and exportable. Wire changes require dual authorization. Segregation of duties is enforced."),
    ("Is the Claude API required?",
     "No. The regex parser handles well-structured PDFs in 5 languages without any API key. Claude is optional for truly unstructured formats."),
    ("How secure is the data?",
     "All data stays on-premise in SQLite. SMTP passwords are session-only. PDF content is HTML-escaped. 4-eye principle enforced at the database layer."),
    ("Can it handle other document types?",
     "Currently PDF-only. Adding Excel or email parsing is a future enhancement; the modular architecture makes it straightforward."),
    ("What's the cost?",
     "Zero for the base system (all open-source). Claude API is optional at ~$0.01-0.03 per PDF. Runs on a single laptop."),
    ("Can multiple people use it simultaneously?",
     "Yes. SQLite WAL mode supports concurrent readers/writers. Streamlit handles multiple browser sessions. Works for teams of 5-10."),
    ("Why Streamlit instead of React?",
     "Speed of development and maintainability. A Python-fluent treasury team can extend it without frontend developers. If scaling to customer-facing, we'd migrate to React."),
    ("Why SQLite instead of PostgreSQL?",
     "For 5-10 users processing 20-40 calls per quarter, SQLite is ideal: zero-config, ships with Python, backup is a file copy. The DB layer is abstracted for easy migration."),
]

for q, a in qas:
    story.append(Paragraph(f'"{q}"', styles["CQuestion"]))
    story.append(Paragraph(a, styles["CAnswer"]))

story.append(PageBreak())

# ══════════════════════════════════════
# SECTION 9: TECHNICAL SPECIFICATIONS
# ══════════════════════════════════════
story.append(Paragraph("9. Technical Specifications", styles["CH1"]))
story.append(make_header_line())

story.append(Paragraph("System Requirements", styles["CH2"]))
req_data = [
    ["Component", "Requirement"],
    ["Python", "3.10 or higher"],
    ["OS", "Windows, macOS, or Linux"],
    ["RAM", "512 MB minimum"],
    ["Disk", "~50 MB (app) + database growth"],
    ["Browser", "Chrome, Firefox, Edge, Safari"],
    ["Network", "Not required (offline-capable, Claude API optional)"],
]
story.append(make_table(req_data[0], req_data[1:], col_widths=[40*mm, 116*mm]))
story.append(Spacer(1, 4*mm))

story.append(Paragraph("Dependencies", styles["CH2"]))
dep_data = [
    ["Package", "Version", "Purpose"],
    ["streamlit", ">=1.30.0", "Web UI framework"],
    ["pandas", ">=2.0.0", "Data manipulation"],
    ["plotly", ">=5.18.0", "Interactive charts"],
    ["pdfplumber", ">=0.10.0", "PDF text extraction"],
    ["rapidfuzz", ">=3.0.0", "Fuzzy string matching"],
    ["openpyxl", ">=3.1.0", "Excel read/write"],
    ["anthropic", "optional", "Claude API for LLM extraction"],
]
story.append(make_table(dep_data[0], dep_data[1:], col_widths=[30*mm, 25*mm, 101*mm]))
story.append(Spacer(1, 4*mm))

story.append(Paragraph("Test Coverage", styles["CH2"]))
test_data = [
    ["Test File", "Tests", "Coverage"],
    ["test_extraction.py", "19", "All 4 PDF notices + edge cases + language detection"],
    ["test_validation.py", "18", "IBAN normalization, fund matching, commitment/wire checks, full pipeline"],
    ["test_database.py", "13", "Table creation, seeding, execution, rejection, duplicate detection"],
    ["Total", "50", "Core extraction, validation, and persistence paths"],
]
story.append(make_table(test_data[0], test_data[1:], col_widths=[35*mm, 15*mm, 106*mm]))
story.append(Spacer(1, 4*mm))

story.append(Paragraph("Codebase Metrics", styles["CH2"]))
code_data = [
    ["File", "Lines", "Purpose"],
    ["app.py", "~1,900", "Main Streamlit application (UI, routing, theme)"],
    ["database.py", "~1,060", "SQLite persistence (10 tables, CRUD, atomic transactions)"],
    ["validation_engine.py", "~175", "Commitment + wire checks, fuzzy matching"],
    ["pdf_extractor.py", "~166", "Multi-language regex PDF parser"],
    ["llm_extractor.py", "~157", "Claude API integration + smart fallback"],
    ["data_loader.py", "~69", "Excel seed data ingestion"],
    ["email_sender.py", "~50", "SMTP email sending"],
    ["Total", "~3,580", "Complete application"],
]
story.append(make_table(code_data[0], code_data[1:], col_widths=[38*mm, 18*mm, 100*mm]))

story.append(Spacer(1, 10*mm))
story.append(make_thin_line())
story.append(Paragraph(
    "Project Sentinel  |  Calibrium AG  |  github.com/SEFICO-23/Sentinel  |  April 2026",
    styles["CFooter"]
))

# ── Build ──
doc.build(story, onFirstPage=on_first_page, onLaterPages=on_page)
print(f"PDF saved to: {OUT_PATH}")
