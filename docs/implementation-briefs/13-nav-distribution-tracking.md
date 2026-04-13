# Brief 13: NAV & Distribution Tracking

## Priority: WAVE 3 | Parallel-Safe | Depends on Wave 2 merge

## Context

Capital calls (cash out) are only half the story. Private equity funds also make distributions (cash back) and report Net Asset Value (NAV). A complete portfolio view tracks all three: commitments, calls, and distributions.

## What to Build

1. **Distributions table** in the database
2. **NAV tracking** per fund
3. **Portfolio summary** section on the Dashboard showing net cash flow
4. **TVPI/DPI metrics** (Total Value to Paid-In, Distributions to Paid-In)

## Implementation

### 1. New database tables

```sql
CREATE TABLE IF NOT EXISTS distributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor TEXT NOT NULL,
    fund_name TEXT NOT NULL,
    amount REAL NOT NULL,
    distribution_type TEXT DEFAULT 'return_of_capital' 
        CHECK(distribution_type IN ('return_of_capital', 'income', 'gain', 'other')),
    value_date TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS nav_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_name TEXT NOT NULL,
    nav_amount REAL NOT NULL,
    reporting_date TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 2. Seed with sample data

Create realistic sample distributions for the existing funds (a few historical distributions per fund).

### 3. Portfolio Summary on Dashboard

Add a new section or tab:
```python
tab_portfolio = st.tabs([..., "Portfolio Summary"])

with tab_portfolio:
    # Per-fund metrics table
    for fund in funds:
        total_called = sum of executed calls for fund
        total_distributed = sum of distributions for fund
        latest_nav = most recent NAV record
        
        dpi = total_distributed / total_called if total_called > 0 else 0
        tvpi = (total_distributed + latest_nav) / total_called if total_called > 0 else 0
    
    # Show as a formatted table with TVPI, DPI, Net Cash Flow
```

### 4. Distribution entry form

Simple form to record distributions (on a new page or in the Dashboard):
```python
with st.expander("Record Distribution"):
    fund = st.selectbox("Fund", fund_names)
    amount = st.number_input("Amount (EUR)", min_value=0)
    dist_type = st.selectbox("Type", ["Return of Capital", "Income", "Gain", "Other"])
    date = st.date_input("Value Date")
    if st.button("Record Distribution"):
        db.add_distribution(...)
```

### 5. Net Cash Flow chart

Line chart showing cumulative capital calls vs cumulative distributions over time.

## Acceptance Criteria

- [ ] Distributions table in database with CRUD
- [ ] NAV records table with CRUD
- [ ] Portfolio summary shows TVPI and DPI per fund
- [ ] Net cash flow chart (calls vs distributions over time)
- [ ] Distribution entry form
- [ ] Sample data seeded for demonstration
- [ ] Existing capital call functionality unchanged
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `database.py` (new tables, seed data, CRUD)
- `app.py` (Dashboard + new section)

## Do NOT

- Modify the capital call processing flow
- Change existing database tables
