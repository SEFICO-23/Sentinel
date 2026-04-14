# Brief 16: Cash Position Forecasting

## Priority: Immediate | Parallel-Safe

## Context

Project Sentinel is a Streamlit-based Treasury Operations dashboard for Private Equity Capital Calls. The project root is `c:\Users\sebas\Desktop\Project Sentinel - Brief and Materials`.

The Dashboard currently shows **current** pending outflows (upcoming capital calls grouped by due date). Treasury needs **forward-looking projections** -- estimated cash needs for the next 3, 6, and 12 months based on historical call patterns.

### Current Architecture
- `app.py` (~1,915 lines) -- Main Streamlit app with all pages
- `database.py` (~1,063 lines) -- SQLite persistence layer with `get_db()` context manager
- `data_loader.py` -- Excel seed data loader
- Data lives in SQLite `sentinel.db` with tables: `commitment_tracker`, `executed_calls`, `processed_calls`, etc.
- Theme uses `dark` boolean from `st.session_state.dark_mode` for CSS variable switching
- All HTML rendered with `unsafe_allow_html=True` must escape user data with the `esc()` function
- Plotly charts must use `title_font` (not deprecated `titlefont`), `font=dict(color=...)` (not `font_color`)
- Chart dark mode: use conditional colors `"#132338" if dark else "white"` for `plot_bgcolor`/`paper_bgcolor`
- Calibrium brand colors: Navy `#1E3161`, Sage `#DDE9E8`, text `#1E3161` / `#5A6B7F`

### Database Schema (relevant tables)
```sql
commitment_tracker(id, investor, fund_name UNIQUE, total_commitment, total_funded_ytd, remaining_open_commitment, updated_at)
executed_calls(id, investor, fund_name, amount, value_date, source, created_at)
```

The `executed_calls` table has ~34 historical records with `value_date` in "DD.MM.YYYY" format spanning 2010-2026.

## What to Build

A **"Cash Forecast"** tab on the Dashboard page that shows:

1. **Forecast KPI cards** -- Projected outflows for next 3, 6, and 12 months
2. **Forecast line chart** -- Monthly projected cash needs with confidence bands (high/low/expected)
3. **Per-fund forecast table** -- Breakdown showing each fund's projected next call amount and date
4. **Remaining commitment runway** -- How many months until each fund is fully called based on historical pace

## Implementation Details

### 1. Add forecasting functions to `database.py`

```python
def get_historical_call_patterns() -> list[dict]:
    """Analyze historical call patterns per fund.
    
    For each fund, calculate:
    - Average call amount
    - Average interval between calls (in days)
    - Standard deviation of amounts
    - Standard deviation of intervals
    - Number of historical calls
    - Date of most recent call
    - Remaining open commitment
    """
    with get_db() as conn:
        funds = conn.execute(
            "SELECT DISTINCT fund_name FROM executed_calls"
        ).fetchall()
        
        patterns = []
        for fund_row in funds:
            fund = fund_row[0]
            calls = conn.execute(
                "SELECT amount, value_date FROM executed_calls WHERE fund_name = ? ORDER BY id",
                (fund,)
            ).fetchall()
            
            # Parse dates, calculate intervals, compute stats
            # ... (parse DD.MM.YYYY format)
            
            commitment = conn.execute(
                "SELECT remaining_open_commitment, total_commitment FROM commitment_tracker WHERE fund_name = ?",
                (fund,)
            ).fetchone()
            
            patterns.append({
                "fund_name": fund,
                "num_calls": len(calls),
                "avg_amount": ...,
                "std_amount": ...,
                "avg_interval_days": ...,
                "std_interval_days": ...,
                "last_call_date": ...,
                "remaining_commitment": commitment[0] if commitment else 0,
                "total_commitment": commitment[1] if commitment else 0,
            })
        return patterns


def generate_cash_forecast(months_ahead: int = 12) -> dict:
    """Generate monthly cash outflow projections.
    
    Returns:
        {
            "monthly_forecast": [
                {"month": "2026-04", "expected": 5000000, "low": 3000000, "high": 7000000},
                ...
            ],
            "fund_forecasts": [
                {"fund_name": "...", "next_call_est": "2026-05", "est_amount": 2000000, 
                 "remaining": 5000000, "runway_months": 18},
                ...
            ],
            "total_3m": ..., "total_6m": ..., "total_12m": ...,
        }
    """
```

**Forecasting logic:**
- For each fund, calculate the average interval between historical calls
- Project the next call date = last_call_date + avg_interval
- Estimate next call amount = average of historical amounts for that fund (capped at remaining commitment)
- Confidence bands: expected +/- 1 standard deviation
- Runway = remaining_commitment / avg_call_amount (in terms of number of calls) * avg_interval
- Aggregate monthly totals across all funds

**Date parsing:** The `value_date` column uses "DD.MM.YYYY" format. Parse with:
```python
from datetime import datetime
datetime.strptime(date_str.strip(), "%d.%m.%Y")
```

### 2. Add a "Cash Forecast" tab in the Dashboard

In `app.py`, the Dashboard page currently has tabs:
```python
tab_tracker, tab_upcoming, tab_executed, tab_portfolio = st.tabs([...])
```

Add a 5th tab:
```python
tab_tracker, tab_upcoming, tab_executed, tab_portfolio, tab_forecast = st.tabs([
    "Commitment Tracker", "Upcoming Calls", "Executed Calls", "Portfolio Summary", "Cash Forecast"
])
```

Inside `with tab_forecast:`:

**KPI cards (3 columns):**
- "3-Month Outlook" -- EUR XM projected
- "6-Month Outlook" -- EUR XM projected  
- "12-Month Outlook" -- EUR XM projected

**Line chart (Plotly):**
- X-axis: months (2026-04 through 2027-03)
- Y-axis: EUR
- Three lines: Expected (solid navy), High estimate (dashed, lighter), Low estimate (dashed, lighter)
- Use `go.Scatter` with `fill='tonexty'` between high and low for confidence band

**Per-fund forecast table:**
| Fund | Last Call | Next Est. | Est. Amount | Remaining | Runway |
|------|-----------|-----------|-------------|-----------|--------|

**Important chart styling:**
```python
chart_bg = "#132338" if dark else "white"
chart_paper = "#0B1929" if dark else "white"
chart_font = "#E8EDF2" if dark else "#1E3161"
chart_grid = "#1E3161" if dark else "#E0E0E0"
```

### 3. Handle edge cases

- Funds with only 1 historical call: use the single amount as estimate, no interval projection (flag as "insufficient data")
- Funds with 0 remaining commitment: exclude from forecast
- Standard deviation of 0: use 10% of mean as confidence band

## Acceptance Criteria

- [ ] `get_historical_call_patterns()` returns stats for all funds with 2+ calls
- [ ] `generate_cash_forecast()` returns monthly projections for 12 months
- [ ] 3 KPI cards show 3/6/12 month totals
- [ ] Line chart shows expected + confidence bands
- [ ] Per-fund table shows next estimated call date and amount
- [ ] Runway column shows months until fully called
- [ ] Chart respects dark/light mode
- [ ] No new pip dependencies (use stdlib statistics module)
- [ ] App runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `database.py` -- Add `get_historical_call_patterns()` and `generate_cash_forecast()`
- `app.py` -- Add "Cash Forecast" tab to Dashboard

## Do NOT

- Add sklearn, numpy, or heavy ML libraries (use stdlib `statistics`)
- Change existing tabs or pages
- Modify the database schema
- Add new sidebar navigation items
