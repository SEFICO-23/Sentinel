# Project Sentinel - Development Conventions

## Overview
Treasury Operations Automation tool for Private Equity Capital Calls. Built with Python/Streamlit, SQLite persistence, and optional Claude API integration.

## Commands
- Run app: `python -m streamlit run app.py`
- Run tests: `pytest tests/ -v`
- Run single test: `pytest tests/test_validation.py -v`
- Delete DB and reset: `del sentinel.db && python -m streamlit run app.py`

## Architecture
- `app.py` imports page modules from `pages/` directory
- All database access goes through `database.py` functions -- never raw SQL in UI code
- PDF extraction: `pdf_extractor.py` (regex) + `llm_extractor.py` (Claude API fallback)
- Validation: `validation_engine.py` with fuzzy fund name matching via rapidfuzz

## Code Style
- All user/PDF-sourced strings must be escaped with `esc()` before embedding in `unsafe_allow_html=True` blocks (XSS prevention)
- Theme-aware CSS uses the `dark` boolean from `st.session_state.dark_mode`
- Plotly charts: use `title_font` (not deprecated `titlefont`), `font=dict(color=...)` (not `font_color`)
- Database mutations must be atomic -- use `with get_db() as conn:` context manager
- New pages: create a module in `pages/`, add to sidebar navigation in `app.py`
- EUR formatting: display as `f"EUR {amount:,.0f}"` in UI, keep raw floats in database/exports

## Database
- SQLite with WAL mode (concurrent read/write safe)
- Schema auto-creates on first run via `db.init_db()`
- Seed data from Excel on first run (checks COUNT(*) > 0 before inserting)
- Migrations for new columns use `PRAGMA table_info` check pattern

## Testing
- Tests use a temporary database (`test_sentinel.db`) that is created and destroyed per test session
- Test PDFs are in `test_notices/` directory
- All 4 original notices must pass/fail as documented in README validation table

## Security
- SMTP passwords: session state only, never persisted to database
- 4-eye principle: reviewer != submitter enforced at both UI and database layer
- Wire changes require dual-authorization with audit trail
