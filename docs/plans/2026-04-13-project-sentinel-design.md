# Project Sentinel - Design Document

## Treasury Operations Automation for Private Equity Capital Calls

**Date:** 13.04.2026
**Version:** 2.0 (Production-Ready)
**Status:** Delivered

---

## 1. Architecture Overview

```
                    ┌──────────────────────────────────┐
                    │        Streamlit Web UI           │
                    │  Dashboard / Process / Wire / Audit│
                    │  + User Selector (RBAC)           │
                    └───────┬──────────┬────────────────┘
                            │          │
              ┌─────────────▼──┐  ┌────▼───────────┐
              │  Smart Extract  │  │  Data Loader   │
              │  Regex + Claude │  │  (openpyxl)    │
              │  (llm_extractor)│  │                │
              └─────────┬──────┘  └────┬───────────┘
                        │              │
                ┌───────▼──────────────▼────────────┐
                │       Validation Engine            │
                │  - Commitment Check                │
                │  - Wire Verification               │
                │  - Fuzzy Fund Name Matching        │
                │  - Zero-Amount Guard               │
                └───────────────┬────────────────────┘
                                │
                ┌───────────────▼────────────────────┐
                │       Database Layer (SQLite)       │
                │  - Commitment Tracker (mutable)    │
                │  - Executed Calls (append-only)    │
                │  - Processed Calls (audit trail)   │
                │  - Users & Roles                   │
                │  + Atomic Transactions             │
                └────────────────────────────────────┘
```

### File Structure

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application (UI, routing, user selection) |
| `database.py` | SQLite persistence with WAL mode, atomic transactions |
| `llm_extractor.py` | Dual-mode extraction: regex primary + Claude API fallback |
| `pdf_extractor.py` | Regex-based PDF parsing (fast, no API key needed) |
| `validation_engine.py` | Commitment + wire checks with fuzzy matching |
| `data_loader.py` | Excel data ingestion (initial seed only) |
| `requirements.txt` | Python dependencies |
| `sentinel.db` | SQLite database (auto-created on first run) |

---

## 2. Key Design Decisions

### 2.1 Dual-Mode Extraction (Regex + LLM)
The system uses regex as the primary extraction method (fast, free, works on well-structured PDFs). When regex returns incomplete data (missing fields), the Claude API is invoked as a fallback. The extraction method and confidence level are displayed in the UI so reviewers know the data provenance.

### 2.2 SQLite Persistence
All state is stored in `sentinel.db` with WAL mode for concurrent read/write safety. The database is seeded from the Excel file on first run, then all mutations (approvals, rejections, commitment updates) are atomic transactions. Data survives browser refreshes and server restarts.

### 2.3 Role-Based 4-Eye Check
Five default users with three roles:
- **Admin** (s.mueller): Can process and review
- **Reviewer** (a.schmidt, m.weber): Can serve as 2nd-eye reviewer
- **Analyst** (l.fischer, t.wagner): Can upload and submit, cannot self-approve

The system enforces that the reviewer must be a different person from the submitter, and only users with `reviewer` or `admin` roles can approve.

### 2.4 Fuzzy Fund Name Matching
Roman numeral normalization (VI -> 6) + rapidfuzz handles the "GT Partners 6 vs VI" mismatch. The matching threshold is 70% with the score displayed in the UI.

### 2.5 Security Hardening
- All PDF-extracted and user-supplied strings are HTML-escaped before rendering
- Two-step confirmation for execution (click -> confirm -> execute)
- Double-execution prevention (database-level check by filename)
- Zero-amount guard prevents silent approval of extraction failures
- XSS prevention via `html.escape()` on all `unsafe_allow_html` blocks

---

## 3. Validation Results for Provided Notices

| Notice | Fund | Amount | Commitment | Wire | Status |
|--------|------|--------|------------|------|--------|
| Notice 1 | GT Partners IV Equity | EUR 5,600,000 | FAIL (exceeds EUR 3.9M by EUR 1.7M) | PASS | REJECTED |
| Notice 2 | GT Partners V Equity | EUR 6,000,000 | PASS (50% of EUR 12M) | FAIL (IBAN mismatch) | REJECTED |
| Notice 3 | Parallax Buyout II | EUR 9,300,000 | PASS (60.8% of EUR 15.3M) | PASS | APPROVED |
| Notice 4 | GT Partners VI Equity | EUR 4,800,000 | PASS (32.4% of EUR 14.8M) | PASS | APPROVED |

### Critical Findings
- **Notice 1:** GP requesting EUR 5.6M against EUR 3.9M remaining -- possible administrative error or commitment increase needed.
- **Notice 2:** IBAN mismatch (German IBAN on PDF vs Swiss IBAN in approved records) -- **potential wire fraud signal**, requires immediate escalation.

---

## 4. Database Schema

```sql
-- Commitment state (mutable, updated on execution)
commitment_tracker(id, investor, fund_name UNIQUE, total_commitment,
                   total_funded_ytd, remaining_open_commitment, updated_at)

-- Historical + new execution records (append-only)
executed_calls(id, investor, fund_name, amount, value_date, source, created_at)

-- Full audit trail of all processed calls
processed_calls(id, filename, fund_name_extracted, fund_name_matched,
                fund_match_score, investor, amount, currency, due_date,
                iban_extracted, iban_approved,
                commitment_passed, commitment_message,
                wire_passed, wire_message,
                overall_status, action, reviewer, review_notes,
                email_body, validation_json, processed_at)

-- User management with roles
users(id, username UNIQUE, display_name, role CHECK(analyst/reviewer/admin),
      active, created_at)
```

---

## 5. Outlooks & Future Features

### 5.1 Near-Term

| Feature | Description |
|---------|-------------|
| **OCR for Scanned PDFs** | Add pytesseract + pdf2image for image-based notices |
| **Multi-Currency + FX** | Support USD/GBP/CHF calls with live FX rate conversion |
| **Batch Upload** | Process multiple PDFs in a queue with batch approval |
| **SMTP Email Integration** | Send confirmation emails directly via Outlook/SMTP |
| **Export to Excel** | Download updated commitment tracker and audit log as .xlsx |

### 5.2 Medium-Term

| Feature | Description |
|---------|-------------|
| **SSO Authentication** | Replace user selector with Azure AD/Okta SSO |
| **Wire Change Management** | Dual-auth workflow for updating approved wire instructions |
| **Cash Position Forecasting** | Predict future cash needs from commitment schedules |
| **Notification Engine** | Slack/Teams alerts for due dates, failures, pending approvals |
| **Regulatory Audit Export** | Generate compliance-ready PDF audit reports |

### 5.3 Long-Term Vision

| Feature | Description |
|---------|-------------|
| **GP Portal API Integration** | Direct API connections to eFront/Investran for electronic notices |
| **ML Anomaly Detection** | Flag unusual call patterns (frequency, amount, timing) |
| **SWIFT MT103 Generation** | Auto-generate SWIFT payment messages from approved calls |
| **Multi-Entity Support** | Manage calls across multiple fund-of-funds entities |
| **Mobile Push Approvals** | Push notification-based approval for reviewers on mobile |

---

## 6. Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Launch (database auto-creates on first run)
python -m streamlit run app.py

# Optional: set Claude API key for LLM extraction
export ANTHROPIC_API_KEY=sk-ant-...
python -m streamlit run app.py

# Test extraction independently
python llm_extractor.py Notice_1_GT_IV_Equity.pdf
```

The application will be available at **http://localhost:8501**.

### Default Users

| Username | Name | Role |
|----------|------|------|
| s.mueller | Sebastian Mueller | Admin |
| a.schmidt | Anna Schmidt | Reviewer |
| m.weber | Max Weber | Reviewer |
| l.fischer | Laura Fischer | Analyst |
| t.wagner | Thomas Wagner | Analyst |
