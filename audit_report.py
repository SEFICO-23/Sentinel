"""
Regulatory Audit PDF Report Generator for Project Sentinel.
Generates a multi-page, Calibrium-branded PDF suitable for external auditors.
"""
import io
import os
from datetime import datetime, date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)

import database as db

# ── Brand Colors (matches create_pdf_handout.py) ──
NAVY = HexColor("#1E3161")
SAGE = HexColor("#DDE9E8")
GREEN = HexColor("#27AE60")
RED = HexColor("#E74C3C")
AMBER = HexColor("#F39C12")
TEXT_DARK = HexColor("#1E3161")
TEXT_LIGHT = HexColor("#5A6B7F")
BORDER = HexColor("#E0E0E0")
WHITE_BG = HexColor("#FFFFFF")
SAGE_BG = HexColor("#F0F5F4")

LOGO_WHITE = os.path.join(os.path.dirname(__file__), "assets", "calibrium_logo_white.png")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "calibrium_logo.png")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# ── Styles ──
_styles = getSampleStyleSheet()

S_TITLE = ParagraphStyle(
    "ATitle", parent=_styles["Title"], fontName="Helvetica-Bold",
    fontSize=28, textColor=NAVY, spaceAfter=6, alignment=TA_LEFT,
)
S_SUBTITLE = ParagraphStyle(
    "ASubtitle", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=14, textColor=TEXT_LIGHT, spaceAfter=20, alignment=TA_LEFT,
)
S_H1 = ParagraphStyle(
    "AH1", parent=_styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=20, textColor=NAVY, spaceBefore=24, spaceAfter=10,
)
S_H2 = ParagraphStyle(
    "AH2", parent=_styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=15, textColor=NAVY, spaceBefore=16, spaceAfter=8,
)
S_BODY = ParagraphStyle(
    "ABody", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=10, textColor=TEXT_DARK, leading=14, spaceAfter=6,
    alignment=TA_JUSTIFY,
)
S_BODY_SM = ParagraphStyle(
    "ABodySm", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=8, textColor=TEXT_DARK, leading=11, spaceAfter=4,
)
S_KPI_LABEL = ParagraphStyle(
    "AKpiLabel", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=9, textColor=TEXT_LIGHT, spaceAfter=2, alignment=TA_CENTER,
)
S_KPI_VALUE = ParagraphStyle(
    "AKpiValue", parent=_styles["Normal"], fontName="Helvetica-Bold",
    fontSize=18, textColor=NAVY, spaceAfter=6, alignment=TA_CENTER,
)
S_FOOTER = ParagraphStyle(
    "AFooter", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=8, textColor=TEXT_LIGHT, alignment=TA_CENTER,
)
S_CERT = ParagraphStyle(
    "ACert", parent=_styles["Normal"], fontName="Helvetica-Oblique",
    fontSize=9, textColor=TEXT_LIGHT, spaceBefore=20, alignment=TA_CENTER,
)


# ── Helpers ──

def _header_line():
    return HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=12)


def _thin_line():
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=8, spaceAfter=8)


def _make_table(headers, rows, col_widths=None):
    """Standard branded table: navy header, alternating rows, gray borders."""
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_DARK),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE_BG, SAGE_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _fmt_eur(val):
    """Format a numeric value as EUR string."""
    try:
        return f"EUR {float(val):,.0f}"
    except (ValueError, TypeError):
        return str(val) if val else "N/A"


def _safe(val, default="—"):
    """Return a safe string for table display."""
    if val is None or val == "":
        return default
    return str(val)


def _status_color(status):
    if status in ("PASS", "EXECUTED"):
        return GREEN
    if status in ("FAIL", "REJECTED"):
        return RED
    if status == "ESCALATED":
        return AMBER
    return TEXT_DARK


# ── Canvas callbacks ──

def _cover_page(canvas, doc, period_from, period_to):
    """Draw cover page: navy banner, logo, titles, CONFIDENTIAL watermark."""
    canvas.saveState()

    # Navy banner
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 100 * mm, PAGE_W, 100 * mm, fill=1)

    # Logo
    if os.path.exists(LOGO_WHITE):
        canvas.drawImage(
            LOGO_WHITE, 20 * mm, PAGE_H - 32 * mm,
            width=50 * mm, height=12 * mm,
            preserveAspectRatio=True, mask="auto",
        )

    # Title text
    canvas.setFont("Helvetica-Bold", 32)
    canvas.setFillColor(white)
    canvas.drawString(20 * mm, PAGE_H - 55 * mm, "Regulatory Audit Report")

    canvas.setFont("Helvetica", 16)
    canvas.setFillColor(SAGE)
    canvas.drawString(20 * mm, PAGE_H - 68 * mm, "Project Sentinel \u2014 Treasury Operations")

    canvas.setFont("Helvetica", 11)
    canvas.setFillColor(HexColor("#B0C4D8"))
    period_str = f"Report Period: {period_from} to {period_to}"
    canvas.drawString(20 * mm, PAGE_H - 82 * mm, period_str)

    gen_str = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    canvas.drawString(20 * mm, PAGE_H - 92 * mm, gen_str)

    # CONFIDENTIAL watermark (diagonal, semi-transparent)
    canvas.saveState()
    canvas.setFillColor(HexColor("#1E316120"))
    canvas.setFont("Helvetica-Bold", 60)
    canvas.translate(PAGE_W / 2, PAGE_H / 2 - 60 * mm)
    canvas.rotate(35)
    canvas.drawCentredString(0, 0, "CONFIDENTIAL")
    canvas.restoreState()

    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.drawString(20 * mm, 12 * mm, "Project Sentinel | Calibrium AG | Confidential")
    canvas.drawRightString(PAGE_W - 20 * mm, 12 * mm, f"Page {doc.page}")

    canvas.restoreState()


def _later_page(canvas, doc):
    """Header line + footer on content pages."""
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(1.5)
    canvas.line(20 * mm, PAGE_H - 15 * mm, PAGE_W - 20 * mm, PAGE_H - 15 * mm)
    # Logo in header
    if os.path.exists(LOGO_PATH):
        canvas.drawImage(
            LOGO_PATH, PAGE_W - 55 * mm, PAGE_H - 14 * mm,
            width=32 * mm, height=8 * mm,
            preserveAspectRatio=True, mask="auto",
        )
    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.drawString(20 * mm, 12 * mm, "Project Sentinel | Calibrium AG | Confidential")
    canvas.drawRightString(PAGE_W - 20 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ── Report Builder ──

def generate_audit_report(
    date_from: str = None,
    date_to: str = None,
    output_path: str = None,
) -> bytes:
    """Generate a regulatory audit PDF report.

    Returns the PDF as bytes (for st.download_button).
    Also saves to output_path if provided.
    """
    # Parse dates
    d_from = None
    d_to = None
    if date_from:
        d_from = date.fromisoformat(date_from)
    if date_to:
        d_to = date.fromisoformat(date_to)

    period_from_str = d_from.strftime("%d %b %Y") if d_from else "All Time"
    period_to_str = d_to.strftime("%d %b %Y") if d_to else datetime.now().strftime("%d %b %Y")

    # ── Fetch data ──
    calls = db.get_processed_calls_filtered(
        date_from=d_from, date_to=d_to,
    )
    commitment = db.get_commitment_tracker()
    users = db.get_users(active_only=False)
    wire_changes = db.get_wire_change_history()
    amendments = db.get_amendment_history()

    # Filter wire changes and amendments to period
    if d_from:
        wire_changes = [w for w in wire_changes if w.get("created_at", "") >= date_from]
        amendments = [a for a in amendments if a.get("created_at", "") >= date_from]
    if d_to:
        wire_changes = [w for w in wire_changes if w.get("created_at", "")[:10] <= date_to]
        amendments = [a for a in amendments if a.get("created_at", "")[:10] <= date_to]

    # ── Build PDF ──
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=22 * mm, bottomMargin=20 * mm,
    )
    story = []

    # ═══════════════════════════════════
    # PAGE 1: COVER
    # ═══════════════════════════════════
    story.append(Spacer(1, 85 * mm))  # space for navy banner drawn on canvas
    story.append(Paragraph(
        f"This document contains a comprehensive audit trail of all capital call "
        f"processing activities within Project Sentinel for the period "
        f"{period_from_str} to {period_to_str}.",
        S_BODY,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        "Contents: Executive Summary, Commitment Tracker Snapshot, "
        "Processed Capital Calls Detail, Wire Changes, Commitment Amendments, "
        "User Activity Summary.",
        S_BODY,
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════
    # PAGE 2: EXECUTIVE SUMMARY
    # ═══════════════════════════════════
    story.append(Paragraph("Executive Summary", S_H1))
    story.append(_header_line())

    story.append(Paragraph(f"<b>Report Period:</b> {period_from_str} to {period_to_str}", S_BODY))
    story.append(Spacer(1, 4 * mm))

    # Aggregate stats
    total_calls = len(calls)
    executed = [c for c in calls if c.get("action") == "EXECUTED"]
    rejected = [c for c in calls if c.get("action") == "REJECTED"]
    escalated = [c for c in calls if c.get("action") == "ESCALATED"]

    def _sum_amounts(call_list):
        total = 0
        for c in call_list:
            try:
                total += float(c.get("amount", 0) or 0)
            except (ValueError, TypeError):
                pass
        return total

    total_eur_executed = _sum_amounts(executed)
    total_eur_rejected = _sum_amounts(rejected)
    total_eur_escalated = _sum_amounts(escalated)

    reviewers_in_period = set(c.get("reviewer", "") for c in calls if c.get("reviewer"))

    # KPI summary table
    kpi_data = [
        ["Metric", "Value"],
        ["Total Capital Calls Processed", str(total_calls)],
        ["Executed", f"{len(executed)}  ({_fmt_eur(total_eur_executed)})"],
        ["Rejected", f"{len(rejected)}  ({_fmt_eur(total_eur_rejected)})"],
        ["Escalated", f"{len(escalated)}  ({_fmt_eur(total_eur_escalated)})"],
        ["Total EUR Executed", _fmt_eur(total_eur_executed)],
        ["Unique Reviewers", str(len(reviewers_in_period))],
        ["Wire Changes in Period", str(len(wire_changes))],
        ["Commitment Amendments in Period", str(len(amendments))],
    ]
    kpi_table = _make_table(kpi_data[0], kpi_data[1:], col_widths=[80 * mm, 80 * mm])
    story.append(kpi_table)
    story.append(Spacer(1, 6 * mm))

    # Key risk events
    story.append(Paragraph("Key Risk Events", S_H2))
    risk_events = []
    for c in calls:
        if c.get("wire_passed") == "FAIL":
            risk_events.append(
                f"<b>Wire Mismatch:</b> {_safe(c.get('filename'))} \u2014 "
                f"{_safe(c.get('wire_message'))}"
            )
        if c.get("commitment_passed") == "FAIL":
            msg = c.get("commitment_message", "")
            if msg and "over" in str(msg).lower():
                risk_events.append(
                    f"<b>Over-Commitment:</b> {_safe(c.get('filename'))} \u2014 "
                    f"{_safe(msg)}"
                )

    if risk_events:
        for evt in risk_events:
            story.append(Paragraph(f"\u2022 {evt}", S_BODY))
    else:
        story.append(Paragraph("No risk events detected in this period.", S_BODY))

    story.append(PageBreak())

    # ═══════════════════════════════════
    # PAGE 3: COMMITMENT TRACKER SNAPSHOT
    # ═══════════════════════════════════
    story.append(Paragraph("Commitment Tracker Snapshot", S_H1))
    story.append(_header_line())
    story.append(Paragraph(
        f"Current state of all fund commitments as of {datetime.now().strftime('%d %b %Y')}.",
        S_BODY,
    ))

    if commitment:
        ct_headers = ["Investor", "Fund", "Total Commitment", "Funded YTD", "Remaining"]
        ct_rows = []
        total_comm = 0
        total_funded = 0
        total_remaining = 0
        for c in commitment:
            comm = float(c.get("total_commitment", 0) or 0)
            funded = float(c.get("total_funded_ytd", 0) or 0)
            remaining = float(c.get("remaining_open_commitment", 0) or 0)
            total_comm += comm
            total_funded += funded
            total_remaining += remaining
            ct_rows.append([
                _safe(c.get("investor")),
                _safe(c.get("fund_name")),
                _fmt_eur(comm),
                _fmt_eur(funded),
                _fmt_eur(remaining),
            ])
        # Totals row
        ct_rows.append([
            "TOTAL", "",
            _fmt_eur(total_comm),
            _fmt_eur(total_funded),
            _fmt_eur(total_remaining),
        ])

        ct_table = _make_table(ct_headers, ct_rows, col_widths=[30 * mm, 40 * mm, 32 * mm, 30 * mm, 30 * mm])
        # Bold the totals row
        last_row = len(ct_rows)
        ct_table.setStyle(TableStyle([
            ("FONTNAME", (0, last_row), (-1, last_row), "Helvetica-Bold"),
            ("BACKGROUND", (0, last_row), (-1, last_row), SAGE),
        ]))
        story.append(ct_table)
        story.append(Spacer(1, 4 * mm))

        pct_deployed = (total_funded / total_comm * 100) if total_comm > 0 else 0
        story.append(Paragraph(
            f"<b>% Deployed:</b> {pct_deployed:.1f}% "
            f"({_fmt_eur(total_funded)} of {_fmt_eur(total_comm)})",
            S_BODY,
        ))
    else:
        story.append(Paragraph("No commitment data available.", S_BODY))

    story.append(PageBreak())

    # ═══════════════════════════════════
    # PAGES 4+: PROCESSED CAPITAL CALLS DETAIL
    # ═══════════════════════════════════
    story.append(Paragraph("Processed Capital Calls \u2014 Detail", S_H1))
    story.append(_header_line())
    story.append(Paragraph(
        f"{total_calls} capital calls processed in the reporting period.",
        S_BODY,
    ))

    if calls:
        detail_headers = [
            "Date", "File", "Fund (Extracted)", "Fund (Matched)", "Score",
            "Amount", "Due Date", "Commit.", "Wire", "Status", "Reviewer",
        ]
        detail_rows = []
        row_statuses = []
        for c in calls:
            ts = _safe(c.get("processed_at", ""))[:16]
            fname = _safe(c.get("filename", ""))
            # Truncate long filenames
            if len(fname) > 22:
                fname = fname[:20] + ".."
            score = c.get("fund_match_score")
            score_str = f"{score}%" if score is not None else "—"
            amount_val = c.get("amount")
            amount_str = _fmt_eur(amount_val) if amount_val else "—"
            due = _safe(c.get("due_date", ""))[:10]
            commit_pass = _safe(c.get("commitment_passed", ""))
            wire_pass = _safe(c.get("wire_passed", ""))
            status = _safe(c.get("action", ""))
            reviewer = _safe(c.get("reviewer", ""))

            detail_rows.append([
                ts, fname,
                _safe(c.get("fund_name_extracted", ""))[:20],
                _safe(c.get("fund_name_matched", ""))[:20],
                score_str, amount_str, due,
                commit_pass, wire_pass, status, reviewer,
            ])
            row_statuses.append(status)

        col_w = [
            22 * mm, 25 * mm, 22 * mm, 22 * mm, 11 * mm,
            20 * mm, 16 * mm, 11 * mm, 10 * mm, 16 * mm, 18 * mm,
        ]
        # Use smaller font for this dense table
        detail_table = _make_table(detail_headers, detail_rows, col_widths=col_w)
        detail_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
        ]))

        # Color-code rows by status
        for i, status in enumerate(row_statuses):
            r = i + 1  # row index (0 = header)
            if status == "EXECUTED":
                detail_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, r), (-1, r), HexColor("#E8F8EF")),
                ]))
            elif status == "REJECTED":
                detail_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, r), (-1, r), HexColor("#FDEDEE")),
                ]))
            elif status == "ESCALATED":
                detail_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, r), (-1, r), HexColor("#FEF5E7")),
                ]))
            # Color the status cell text
            col_idx = 9  # Status column
            detail_table.setStyle(TableStyle([
                ("TEXTCOLOR", (col_idx, r), (col_idx, r), _status_color(status)),
                ("FONTNAME", (col_idx, r), (col_idx, r), "Helvetica-Bold"),
            ]))
            # Color commitment and wire cells
            commit_val = detail_rows[i][7]
            wire_val = detail_rows[i][8]
            detail_table.setStyle(TableStyle([
                ("TEXTCOLOR", (7, r), (7, r), _status_color(commit_val)),
                ("FONTNAME", (7, r), (7, r), "Helvetica-Bold"),
                ("TEXTCOLOR", (8, r), (8, r), _status_color(wire_val)),
                ("FONTNAME", (8, r), (8, r), "Helvetica-Bold"),
            ]))

        story.append(detail_table)
        story.append(Spacer(1, 4 * mm))

        # Review notes detail (if any calls have notes)
        calls_with_notes = [c for c in calls if c.get("review_notes")]
        if calls_with_notes:
            story.append(Paragraph("Review Notes", S_H2))
            for c in calls_with_notes:
                story.append(Paragraph(
                    f"<b>{_safe(c.get('filename'))}:</b> {_safe(c.get('review_notes'))}",
                    S_BODY_SM,
                ))
    else:
        story.append(Paragraph("No capital calls processed in this period.", S_BODY))

    # ═══════════════════════════════════
    # WIRE CHANGES SECTION
    # ═══════════════════════════════════
    if wire_changes:
        story.append(PageBreak())
        story.append(Paragraph("Wire Change Requests", S_H1))
        story.append(_header_line())
        story.append(Paragraph(
            f"{len(wire_changes)} wire change request(s) in the reporting period.",
            S_BODY,
        ))

        wc_headers = ["Date", "Fund", "Field", "Old Value", "New Value",
                       "Reason", "Requested By", "Reviewed By", "Status"]
        wc_rows = []
        for w in wire_changes:
            wc_rows.append([
                _safe(w.get("created_at", ""))[:16],
                _safe(w.get("fund_name", "")),
                _safe(w.get("field_changed", "")),
                _safe(w.get("old_value", "")),
                _safe(w.get("new_value", "")),
                _safe(w.get("reason", "")),
                _safe(w.get("requested_by", "")),
                _safe(w.get("reviewed_by", "")),
                _safe(w.get("status", "")),
            ])
        wc_widths = [20 * mm, 22 * mm, 16 * mm, 20 * mm, 20 * mm,
                     24 * mm, 16 * mm, 16 * mm, 14 * mm]
        wc_table = _make_table(wc_headers, wc_rows, col_widths=wc_widths)
        wc_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
        ]))
        story.append(wc_table)

    # ═══════════════════════════════════
    # COMMITMENT AMENDMENTS SECTION
    # ═══════════════════════════════════
    if amendments:
        story.append(PageBreak())
        story.append(Paragraph("Commitment Amendments", S_H1))
        story.append(_header_line())
        story.append(Paragraph(
            f"{len(amendments)} commitment amendment(s) in the reporting period.",
            S_BODY,
        ))

        am_headers = ["Date", "Fund", "Current", "Increase", "New Total",
                       "Reason", "Requested By", "Reviewed By", "Status"]
        am_rows = []
        for a in amendments:
            am_rows.append([
                _safe(a.get("created_at", ""))[:16],
                _safe(a.get("fund_name", "")),
                _fmt_eur(a.get("current_commitment")),
                _fmt_eur(a.get("requested_increase")),
                _fmt_eur(a.get("new_commitment")),
                _safe(a.get("reason", "")),
                _safe(a.get("requested_by", "")),
                _safe(a.get("reviewed_by", "")),
                _safe(a.get("status", "")),
            ])
        am_widths = [20 * mm, 22 * mm, 18 * mm, 18 * mm, 18 * mm,
                     24 * mm, 16 * mm, 16 * mm, 14 * mm]
        am_table = _make_table(am_headers, am_rows, col_widths=am_widths)
        am_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
        ]))
        story.append(am_table)

    # ═══════════════════════════════════
    # FINAL PAGE: USER ACTIVITY SUMMARY
    # ═══════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("User Activity Summary", S_H1))
    story.append(_header_line())

    if users:
        # Count processed/reviewed calls per user
        user_counts = {}
        for u in users:
            uname = u.get("display_name") or u.get("username", "")
            user_counts[uname] = {
                "role": u.get("role", ""),
                "processed": 0,
                "reviewed": 0,
            }
        for c in calls:
            reviewer = c.get("reviewer", "")
            if reviewer and reviewer in user_counts:
                user_counts[reviewer]["reviewed"] += 1

        ua_headers = ["User", "Role", "Calls Reviewed"]
        ua_rows = []
        for uname, info in sorted(user_counts.items()):
            ua_rows.append([
                uname,
                info["role"].title() if info["role"] else "—",
                str(info["reviewed"]),
            ])
        ua_table = _make_table(ua_headers, ua_rows, col_widths=[55 * mm, 40 * mm, 35 * mm])
        story.append(ua_table)
    else:
        story.append(Paragraph("No user data available.", S_BODY))

    story.append(Spacer(1, 15 * mm))
    story.append(_thin_line())
    story.append(Paragraph(
        "This report was auto-generated by Project Sentinel.",
        S_CERT,
    ))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Calibrium AG | Confidential",
        S_FOOTER,
    ))

    # ── Build ──
    def _on_first(canvas, doc):
        _cover_page(canvas, doc, period_from_str, period_to_str)

    doc.build(story, onFirstPage=_on_first, onLaterPages=_later_page)

    pdf_bytes = buf.getvalue()
    buf.close()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
