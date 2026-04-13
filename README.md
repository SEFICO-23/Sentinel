# Project Sentinel

**Treasury Operations Automation for Private Equity Capital Calls**

A web-based tool built with Python/Streamlit that automates the processing, validation, and approval of PE capital call notices. Designed to replace manual workflows with AI-driven data extraction, automated risk controls, and a human-in-the-loop approval process.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the application (database auto-creates on first run)
python -m streamlit run app.py

# Optional: enable AI-powered PDF extraction
export ANTHROPIC_API_KEY=sk-ant-...
python -m streamlit run app.py
```

The app opens at **http://localhost:8501**. Default users are pre-seeded (see [Users](#default-users) below).

---

## What It Does

### 1. PDF Ingestion & AI Extraction
Upload capital call PDF notices via drag-and-drop. The system extracts structured data using a dual-mode approach:
- **Regex parser** (primary) -- fast, free, handles well-structured notices in EN/DE/FR/IT/ES
- **Claude API** (fallback) -- handles messy, unstructured, or scanned notices when regex fails

Extracted fields: Fund Name, Amount, Currency, Due Date, Bank, SWIFT/BIC, IBAN.

### 2. Automated Validation Engine
Every notice runs through two automated checks before a human sees it:
- **Commitment Check** -- verifies the requested amount is within the fund's remaining open commitment
- **Wire Verification** -- compares the IBAN on the PDF against the approved wire instructions database, with normalized matching

Fuzzy fund name matching handles variations like "GT Partners **6** Equity" vs "GT Partners **VI** Equity" using Roman numeral normalization and rapidfuzz scoring.

### 3. 4-Eye Approval Workflow
Role-based access with three tiers:
| Role | Can Upload | Can Approve | Can Manage Users |
|------|-----------|-------------|-----------------|
| Analyst | Yes | No | No |
| Reviewer | Yes | Yes | No |
| Admin | Yes | Yes | Yes |

The system enforces that the reviewer must be a **different person** from the submitter. Two-step confirmation prevents accidental execution of multi-million EUR payments.

### 4. Risk Controls
| Control | What It Catches |
|---------|----------------|
| Commitment check | Amount exceeds remaining open commitment |
| Wire verification | IBAN mismatch (potential fraud) |
| Duplicate detection | Same fund/amount/date already processed |
| Zero-amount guard | Missing or unparseable amount fields |
| Wire change management | Unauthorized changes to banking details |
| Commitment amendments | Formal workflow for increasing commitments |

### 5. Reporting & Audit
- **Dashboard** with KPI cards, charts, vintage filters, cash position forecasting
- **Audit log** with filtering, pagination, and full validation trail
- **Excel export** (single sheet or multi-sheet report)
- **Email confirmation** generation with optional SMTP sending
- **PDF archive** with downloadable originals from audit log

---

## Architecture

```
app.py                 Streamlit UI (pages, routing, theme)
  |
  +-- pages/           Page modules (dashboard, process, audit, etc.)
  |
  +-- database.py      SQLite persistence (WAL mode, atomic transactions)
  +-- pdf_extractor.py Regex-based PDF parser (multi-language)
  +-- llm_extractor.py Claude API integration + smart fallback
  +-- validation_engine.py  Commitment + wire checks, fuzzy matching
  +-- email_sender.py  SMTP email sending
  +-- data_loader.py   Excel seed data ingestion
  |
  +-- sentinel.db      SQLite database (auto-created)
  +-- archive/         Stored PDF originals
```

### Database Schema

```
commitment_tracker   -- Mutable fund commitment state
executed_calls       -- Historical + new payment records (append-only)
processed_calls      -- Full audit trail of all processed notices
approved_wires       -- Verified counterparty banking details
wire_change_requests -- Wire update workflow with dual-authorization
commitment_amendments -- Commitment increase workflow
users                -- Role-based user management
distributions        -- Fund distribution tracking
nav_records          -- Net Asset Value snapshots
gp_contacts          -- Counterparty contact directory
```

---

## Default Users

| Username | Name | Role |
|----------|------|------|
| s.mueller | Sebastian Mueller | Admin |
| a.schmidt | Anna Schmidt | Reviewer |
| m.weber | Max Weber | Reviewer |
| l.fischer | Laura Fischer | Analyst |
| t.wagner | Thomas Wagner | Analyst |

---

## Validation Test Results

The system is tested against 4 capital call notices with deliberately planted validation traps:

| Notice | Fund | Amount | Commitment | Wire | Result |
|--------|------|--------|------------|------|--------|
| Notice 1 | GT Partners IV Equity | EUR 5.6M | FAIL (exceeds EUR 3.9M remaining) | PASS | Rejected |
| Notice 2 | GT Partners V Equity | EUR 6.0M | PASS | FAIL (IBAN mismatch -- fraud signal) | Rejected |
| Notice 3 | Parallax Buyout II | EUR 9.3M | PASS | PASS | Approved |
| Notice 4 | GT Partners VI Equity | EUR 4.8M | PASS (fuzzy match: "6" -> "VI") | PASS | Approved |

---

## Features

| Feature | Description |
|---------|-------------|
| Dark/Light mode | Toggle in sidebar with full theme support |
| Batch upload | Process 10-20 PDFs at once with summary table |
| Due date alerts | Color-coded urgency badges, overdue detection |
| Cash position | Pending outflow forecasting by date and investor |
| PDF preview | Side-by-side view of original PDF and extracted data |
| Wire change management | Dual-authorization workflow for banking detail updates |
| Commitment amendments | Formal increase requests when calls exceed limits |
| Portfolio summary | TVPI/DPI metrics, cumulative cash flow charts |
| GP contact directory | Quick-access contacts for escalation on failures |
| Multi-language PDFs | Regex patterns for EN, DE, FR, IT, ES notices |
| Duplicate detection | Exact and fuzzy matching with override workflow |
| PDF archive | Persistent storage with download from audit log |
| Excel export | Single or multi-sheet reports with formatted data |
| Email integration | SMTP sending with HTML templates |
| Audit log search | Filter by date, fund, status, reviewer with pagination |

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Tech Stack

- **Python 3.10+**
- **Streamlit** -- Web UI framework
- **SQLite** -- Persistence (WAL mode for concurrent access)
- **Plotly** -- Interactive charts
- **pdfplumber** -- PDF text extraction
- **rapidfuzz** -- Fuzzy string matching
- **openpyxl** -- Excel read/write
- **Anthropic SDK** -- Claude API for LLM extraction (optional)

---

## Project Structure

```
Project Sentinel/
+-- app.py                          # Main application
+-- pages/                          # Page modules
|   +-- dashboard.py
|   +-- process_capital_call.py
|   +-- wire_instructions.py
|   +-- audit_log.py
|   +-- amendments.py
|   +-- gp_contacts.py
|   +-- portfolio.py
+-- database.py                     # SQLite persistence layer
+-- pdf_extractor.py                # Regex PDF parser
+-- llm_extractor.py                # LLM extraction with fallback
+-- validation_engine.py            # Risk control checks
+-- email_sender.py                 # SMTP integration
+-- data_loader.py                  # Excel seed data
+-- tests/                          # Test suite
|   +-- test_extraction.py
|   +-- test_validation.py
|   +-- test_database.py
+-- test_notices/                   # Diverse format test PDFs
+-- docs/                           # Design documents
+-- .streamlit/config.toml          # Streamlit theme config
+-- requirements.txt                # Dependencies
+-- CLAUDE.md                       # AI development conventions
+-- README.md                       # This file
```
