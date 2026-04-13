# Brief 03: Due Date Countdown & Alerts

## Priority: WAVE 1 | Parallel-Safe | No Dependencies

## Context

Capital calls have hard deadlines with penalty clauses for late payment. Treasury needs visual urgency indicators on upcoming calls so nothing slips through.

## What to Build

1. **Color-coded urgency badges** on the Upcoming Capital Calls table
2. **Countdown display** showing days until due
3. **Alert banner** at the top of the Dashboard when any call is due within 3 days
4. **Overdue detection** for calls past their due date

## Implementation

### 1. Parse due dates

The "Due Date" column in the upcoming calls DataFrame is stored as strings like "16.03.2026". Parse them:
```python
from datetime import datetime, timedelta

def parse_due_date(date_str):
    """Parse DD.MM.YYYY date string."""
    try:
        return datetime.strptime(str(date_str).strip(), "%d.%m.%Y")
    except (ValueError, AttributeError):
        return None

def days_until(date_str):
    due = parse_due_date(date_str)
    if due is None:
        return None
    return (due - datetime.now()).days
```

### 2. Urgency classification

```python
def urgency_badge(days):
    if days is None:
        return "unknown", "badge-info"
    if days < 0:
        return f"OVERDUE ({abs(days)}d)", "badge-fail"
    if days <= 3:
        return f"URGENT ({days}d)", "badge-fail"
    if days <= 7:
        return f"SOON ({days}d)", "badge-warn"
    return f"{days} days", "badge-pass"
```

### 3. Dashboard alert banner

At the top of the Dashboard page (before KPI cards), check for urgent calls:
```python
urgent_calls = [call for call in upcoming_data if days_until(call["Due Date"]) is not None and days_until(call["Due Date"]) <= 3]
if urgent_calls:
    st.error(f"**{len(urgent_calls)} capital call(s) due within 3 days!** Review the Upcoming Calls tab immediately.")
```

### 4. Enhanced Upcoming Calls table

Add "Days Until Due" and "Urgency" columns to the upcoming calls display with color-coded badges rendered via `st.markdown()`.

### 5. Theme-aware colors

Use the existing `dark` boolean to ensure urgency badges are readable in both light and dark mode. The badge classes (`badge-fail`, `badge-warn`, `badge-pass`) already support both themes.

## Acceptance Criteria

- [ ] Upcoming Calls table shows "Days Until Due" column
- [ ] Urgency badges: red for <=3 days/overdue, amber for <=7 days, green for >7 days
- [ ] Alert banner appears at top of Dashboard when any call is due within 3 days
- [ ] Overdue calls are clearly marked as "OVERDUE (Xd)"
- [ ] Works correctly in both light and dark mode
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `app.py` (Dashboard page, Upcoming Calls section)

## Do NOT

- Change the database schema
- Modify any other files
- Add new pages to the sidebar
