# Project Sentinel - Implementation Orchestrator

## How to Use This Document

This is the **master coordination file** for implementing all remaining features of Project Sentinel. Each numbered brief below is a self-contained task that can be given to a fresh Claude Code session.

### Parallel Execution Strategy

```
                    ┌──────────────────────────────┐
                    │   WAVE 1 (All in Parallel)   │
                    ├──────────────────────────────┤
                    │ Brief 01: Export to Excel    │
                    │ Brief 02: Batch PDF Upload   │
                    │ Brief 03: Due Date Alerts    │
                    │ Brief 04: Cash Position      │
                    │ Brief 05: PDF Preview Panel  │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │   WAVE 2 (All in Parallel)   │
                    │   (after Wave 1 merges)      │
                    ├──────────────────────────────┤
                    │ Brief 06: Email Integration  │
                    │ Brief 07: Wire Change Mgmt   │
                    │ Brief 08: Commitment Amend   │
                    │ Brief 09: Audit Log Search   │
                    │ Brief 10: Dashboard Filters  │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │   WAVE 3 (All in Parallel)   │
                    ├──────────────────────────────┤
                    │ Brief 11: Multi-Lang PDFs    │
                    │ Brief 12: Duplicate Detection│
                    │ Brief 13: NAV/Distribution   │
                    │ Brief 14: GP Contact Dir     │
                    │ Brief 15: PDF Archive        │
                    └──────────────────────────────┘
```

### How to Launch a Session

For each brief, open a fresh Claude Code session and paste:

```
Read the implementation brief at:
docs/implementation-briefs/XX-feature-name.md

Then implement it following the instructions exactly.
When done, verify by running the app with:
python -m streamlit run app.py
```

### Wave Dependencies

- **Wave 1**: No dependencies. All briefs can run simultaneously.
- **Wave 2**: Depends on Wave 1 being merged. Brief 08 (Commitment Amendment) depends on the approval workflow from the base app. Brief 07 (Wire Change) depends on the database schema from the base app.
- **Wave 3**: Depends on Wave 2 being merged. Brief 12 (Duplicate Detection) depends on the audit log schema. Brief 15 (PDF Archive) depends on the database layer.

### Merge Strategy

After each wave completes:
1. Review each session's changes
2. Merge into main codebase (resolve any conflicts in `app.py` by combining sidebar additions and page additions)
3. Run `python -m streamlit run app.py` and test all features
4. Proceed to next wave

### Current Architecture (All Sessions Must Know This)

```
Project Sentinel/
├── app.py                    # Main Streamlit app (UI, routing, themes)
├── database.py               # SQLite persistence (WAL mode, atomic transactions)
├── llm_extractor.py          # Dual-mode extraction (regex + Claude API)
├── pdf_extractor.py          # Regex-based PDF parser
├── validation_engine.py      # Commitment + wire checks, fuzzy matching
├── data_loader.py            # Excel ingestion (initial seed only)
├── requirements.txt          # Python dependencies
├── sentinel.db               # SQLite database (auto-created)
├── IO_Case_study_Capital_Calls.xlsx  # Source data
├── Notice_*.pdf              # Sample capital call PDFs
└── docs/
    ├── plans/                # Design documents
    └── implementation-briefs/# These files
```

### Database Schema

```sql
commitment_tracker(id, investor, fund_name UNIQUE, total_commitment,
                   total_funded_ytd, remaining_open_commitment, updated_at)

executed_calls(id, investor, fund_name, amount, value_date, source, created_at)

processed_calls(id, filename, fund_name_extracted, fund_name_matched,
                fund_match_score, investor, amount, currency, due_date,
                iban_extracted, iban_approved,
                commitment_passed, commitment_message,
                wire_passed, wire_message,
                overall_status, action, reviewer, review_notes,
                email_body, validation_json, processed_at)

users(id, username UNIQUE, display_name, role CHECK(analyst/reviewer/admin),
      active, created_at)
```

### Key Conventions

- All HTML rendered via `st.markdown(..., unsafe_allow_html=True)` must escape user/PDF data with the `esc()` function
- Theme-aware CSS uses the `dark` boolean variable (from `st.session_state.dark_mode`)
- Database access goes through `database.py` functions, never raw SQL in `app.py`
- New pages are added as `elif page == "Page Name":` blocks in `app.py`
- New sidebar entries are added to the `st.radio()` options list
- Add `pip` dependencies to `requirements.txt`
