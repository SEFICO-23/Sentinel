# Brief 18: ML Anomaly Detection

## Priority: Immediate | Parallel-Safe

## Context

Project Sentinel is a Streamlit-based Treasury Operations dashboard for Private Equity Capital Calls. The project root is `c:\Users\sebas\Desktop\Project Sentinel - Brief and Materials`.

The system currently uses **rule-based** validation (commitment check, wire verification, duplicate detection). These catch known-bad patterns. What's missing is **pattern-based** detection that flags calls that are technically valid but statistically unusual -- the kind of thing a human might notice after years of experience.

### Current Architecture
- `app.py` (~1,915 lines) -- Main Streamlit app
- `database.py` (~1,063 lines) -- SQLite persistence
- `validation_engine.py` (~175 lines) -- Commitment + wire checks, fuzzy matching
- `pdf_extractor.py` (~166 lines) -- Multi-language regex parser
- Theme uses `dark` boolean; Calibrium brand: Navy `#1E3161`, Sage `#DDE9E8`
- All HTML rendered with `unsafe_allow_html=True` must escape user data with `esc()`
- Plotly: use `title_font` (not `titlefont`), `font=dict(color=...)` (not `font_color`)

### Database Schema (relevant tables)
```sql
executed_calls(id, investor, fund_name, amount, value_date, source, created_at)
commitment_tracker(id, investor, fund_name, total_commitment, total_funded_ytd, remaining_open_commitment)
processed_calls(id, filename, fund_name_matched, amount, due_date, overall_status, action, processed_at)
```

The `executed_calls` table has ~34 historical records spanning 2010-2026.

### Existing validation flow in app.py
After extraction and before the approval workflow, the app shows validation results in two cards (commitment check + wire check). The anomaly detection should appear as a **third card** in that row.

## What to Build

A new module `anomaly_detector.py` that scores capital calls on three statistical dimensions, plus UI integration showing anomaly warnings during processing.

## Implementation Details

### 1. Create `anomaly_detector.py`

```python
"""
Statistical anomaly detection for capital call notices.
Uses z-scores and IQR analysis on historical patterns.
No external ML libraries -- pure Python stdlib (statistics module).
"""
from statistics import mean, stdev, median
from datetime import datetime
import database as db


def detect_anomalies(fund_name: str, amount: float, due_date: str = None) -> dict:
    """Score a capital call for anomalies based on historical patterns.
    
    Returns:
        {
            "overall_risk": "low" | "medium" | "high",
            "overall_score": 0-100 (0=normal, 100=extreme anomaly),
            "signals": [
                {
                    "type": "amount",
                    "severity": "low" | "medium" | "high",
                    "score": 0-100,
                    "message": "...",
                    "detail": "..."
                },
                ...
            ]
        }
    """
```

### 2. Three anomaly signals

**Signal 1: Amount Anomaly (z-score)**

Compare the call amount against the fund's historical call amounts.

```python
def _check_amount_anomaly(fund_name: str, amount: float) -> dict:
    """Check if amount deviates significantly from historical average."""
    # Get historical amounts for this fund
    history = db.get_executed_calls_for_fund(fund_name)  # Need to add this function
    amounts = [h["amount"] for h in history]
    
    if len(amounts) < 2:
        return {"type": "amount", "severity": "low", "score": 0,
                "message": "Insufficient history", "detail": "Less than 2 historical calls"}
    
    avg = mean(amounts)
    sd = stdev(amounts) if len(amounts) >= 3 else avg * 0.15
    
    if sd == 0:
        sd = avg * 0.1  # Prevent division by zero
    
    z = abs(amount - avg) / sd
    
    # Score: z=0 -> 0, z=1 -> 25, z=2 -> 50, z=3 -> 75, z>=4 -> 100
    score = min(100, int(z * 25))
    
    if z >= 3:
        severity = "high"
        msg = f"Amount EUR {amount:,.0f} is {z:.1f} std devs from average EUR {avg:,.0f}"
    elif z >= 2:
        severity = "medium"
        msg = f"Amount EUR {amount:,.0f} is notably different from average EUR {avg:,.0f}"
    else:
        severity = "low"
        msg = f"Amount EUR {amount:,.0f} is within normal range (avg EUR {avg:,.0f})"
    
    return {
        "type": "amount", "severity": severity, "score": score,
        "message": msg,
        "detail": f"Historical: {len(amounts)} calls, avg EUR {avg:,.0f}, std EUR {sd:,.0f}, z-score: {z:.2f}"
    }
```

**Signal 2: Timing Anomaly (interval check)**

Check if the call arrives much sooner or later than expected based on historical call frequency.

```python
def _check_timing_anomaly(fund_name: str, due_date: str = None) -> dict:
    """Check if call timing deviates from historical interval pattern."""
    history = db.get_executed_calls_for_fund(fund_name)
    
    if len(history) < 3:
        return {"type": "timing", "severity": "low", "score": 0,
                "message": "Insufficient history for timing analysis",
                "detail": "Need 3+ calls to establish interval pattern"}
    
    # Parse dates and calculate intervals
    dates = []
    for h in history:
        try:
            d = datetime.strptime(str(h["value_date"]).strip(), "%d.%m.%Y")
            dates.append(d)
        except (ValueError, AttributeError):
            continue
    
    dates.sort()
    intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
    
    if not intervals:
        return {"type": "timing", "severity": "low", "score": 0,
                "message": "Could not parse historical dates", "detail": ""}
    
    avg_interval = mean(intervals)
    last_call = dates[-1]
    days_since_last = (datetime.now() - last_call).days
    
    # How many average intervals have passed?
    if avg_interval > 0:
        ratio = days_since_last / avg_interval
    else:
        ratio = 1.0
    
    # Score based on deviation from expected interval
    deviation = abs(ratio - 1.0)
    score = min(100, int(deviation * 50))
    
    if ratio < 0.3:
        severity = "high"
        msg = f"Call arrived very early: {days_since_last} days since last (avg interval: {avg_interval:.0f} days)"
    elif ratio > 2.5:
        severity = "medium"
        msg = f"Unusually long gap: {days_since_last} days since last call (avg: {avg_interval:.0f} days)"
    else:
        severity = "low"
        msg = f"Timing is normal: {days_since_last} days since last call (avg: {avg_interval:.0f} days)"
    
    return {
        "type": "timing", "severity": severity, "score": score,
        "message": msg,
        "detail": f"Historical intervals: {len(intervals)} gaps, avg {avg_interval:.0f} days, range {min(intervals)}-{max(intervals)} days"
    }
```

**Signal 3: Frequency Anomaly (burst detection)**

Check if there have been too many calls for one fund in a short period.

```python
def _check_frequency_anomaly(fund_name: str) -> dict:
    """Check if there's an unusual burst of calls for this fund."""
    # Count calls in last 30, 90, 365 days
    history = db.get_executed_calls_for_fund(fund_name)
    
    now = datetime.now()
    calls_30d = 0
    calls_90d = 0
    
    for h in history:
        try:
            d = datetime.strptime(str(h["value_date"]).strip(), "%d.%m.%Y")
            delta = (now - d).days
            if delta <= 30: calls_30d += 1
            if delta <= 90: calls_90d += 1
        except (ValueError, AttributeError):
            continue
    
    # Also count processed_calls (pending approvals)
    # to detect someone submitting many calls rapidly
    
    score = 0
    if calls_30d >= 3:
        severity = "high"
        score = 80
        msg = f"Burst: {calls_30d} calls in the last 30 days"
    elif calls_90d >= 4:
        severity = "medium"
        score = 50
        msg = f"Elevated frequency: {calls_90d} calls in the last 90 days"
    else:
        severity = "low"
        msg = f"Normal frequency: {calls_30d} calls in 30d, {calls_90d} in 90d"
    
    return {
        "type": "frequency", "severity": severity, "score": score,
        "message": msg,
        "detail": f"Last 30 days: {calls_30d} calls, last 90 days: {calls_90d} calls"
    }
```

**Overall risk scoring:**
```python
def _compute_overall_risk(signals: list[dict]) -> tuple[str, int]:
    max_score = max(s["score"] for s in signals) if signals else 0
    avg_score = sum(s["score"] for s in signals) / len(signals) if signals else 0
    # Overall = weighted toward max (catches single extreme anomaly)
    overall = int(max_score * 0.6 + avg_score * 0.4)
    
    if overall >= 60: return "high", overall
    if overall >= 30: return "medium", overall
    return "low", overall
```

### 3. Add helper query to `database.py`

```python
def get_executed_calls_for_fund(fund_name: str) -> list[dict]:
    """Get all executed calls for a specific fund."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT amount, value_date FROM executed_calls WHERE fund_name = ? ORDER BY id",
            (fund_name,)
        ).fetchall()
        return [dict(r) for r in rows]
```

### 4. Integrate into `app.py` -- Process Capital Call page

After the existing validation results (commitment check + wire check cards), add a third card:

```python
# After the v1, v2 = st.columns(2) block with commitment and wire cards,
# add the anomaly detection:

if validation["fund_name_matched"]:
    from anomaly_detector import detect_anomalies
    anomaly = detect_anomalies(
        validation["fund_name_matched"],
        validation["amount"],
        validation.get("due_date")
    )
    
    st.markdown('<div class="section-header">3. Anomaly Analysis</div>', unsafe_allow_html=True)
    
    # Overall risk badge
    risk_colors = {"low": "badge-pass", "medium": "badge-warn", "high": "badge-fail"}
    risk_class = risk_colors.get(anomaly["overall_risk"], "badge-info")
    st.markdown(
        f'Anomaly Risk: <span class="badge {risk_class}">'
        f'{anomaly["overall_risk"].upper()} ({anomaly["overall_score"]}/100)</span>',
        unsafe_allow_html=True,
    )
    
    # Signal cards (3 columns)
    a1, a2, a3 = st.columns(3)
    for col, signal in zip([a1, a2, a3], anomaly["signals"]):
        with col:
            severity_class = "val-pass" if signal["severity"] == "low" else ("val-fail" if signal["severity"] == "high" else "val-card")
            icon = "&#10003;" if signal["severity"] == "low" else ("&#9888;" if signal["severity"] == "medium" else "&#10007;")
            st.markdown(f"""
            <div class="val-card {severity_class}" style="border-left-color: {'#27AE60' if signal['severity'] == 'low' else ('#F39C12' if signal['severity'] == 'medium' else '#E74C3C')};">
                <h4 style="margin:0 0 0.3rem 0; font-size: 0.9rem;">{icon} {esc(signal['type'].title())} Check</h4>
                <p style="margin:0 0 0.2rem 0; font-size: 0.85rem; color: var(--text-secondary);">{esc(signal['message'])}</p>
                <p style="margin:0; font-size: 0.75rem; color: var(--text-muted);">{esc(signal['detail'])}</p>
            </div>
            """, unsafe_allow_html=True)
```

### 5. Section numbering update

The existing sections in the Process Capital Call page are numbered:
- "1. Extracted Data"
- "2. Validation Results"  
- "3. Approval Workflow"

Insert "3. Anomaly Analysis" between validation and approval, renumbering approval to "4. Approval Workflow".

### 6. Anomaly impact on approval

Anomalies should **warn but not block**. Even high-anomaly calls can be approved if both commitment and wire checks pass. The anomaly score is informational for the reviewer.

If anomaly risk is "high", add a yellow warning box:
```python
if anomaly["overall_risk"] == "high":
    st.warning("This capital call has unusual statistical characteristics. Review the anomaly signals carefully before approving.")
```

## Acceptance Criteria

- [ ] `anomaly_detector.py` created with `detect_anomalies()` function
- [ ] Three signals implemented: amount, timing, frequency
- [ ] Z-score calculation for amount anomaly
- [ ] Interval analysis for timing anomaly
- [ ] Burst detection for frequency anomaly
- [ ] Overall risk score computed (0-100 scale)
- [ ] Three anomaly cards displayed on Process Capital Call page
- [ ] Risk badge shows LOW/MEDIUM/HIGH with color coding
- [ ] Warning banner for high-anomaly calls
- [ ] Anomalies are informational only (don't block approval)
- [ ] Works for single-file and batch upload flows
- [ ] `get_executed_calls_for_fund()` added to database.py
- [ ] No sklearn/numpy dependencies (stdlib `statistics` only)
- [ ] App runs without errors: `python -m streamlit run app.py`

## Files to Create

- `anomaly_detector.py` -- Anomaly scoring module

## Files to Modify

- `database.py` -- Add `get_executed_calls_for_fund()` query
- `app.py` -- Add anomaly cards to Process Capital Call page (single + batch flows)

## Do NOT

- Block approval based on anomaly scores (warn only)
- Add sklearn, numpy, or heavy ML libraries
- Change the database schema
- Modify the validation engine (anomaly detection is separate from validation)
- Remove or change existing validation cards
