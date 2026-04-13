# Brief 01: Export to Excel

## Priority: WAVE 1 | Parallel-Safe | No Dependencies

## Context

Project Sentinel is a Streamlit-based Treasury Operations dashboard for processing Private Equity Capital Calls. Treasury teams need to export data to Excel for reporting, email attachments, and offline analysis.

## What to Build

Add "Download as Excel" buttons to the Dashboard page for:
1. **Commitment Tracker** - Current state with all columns + % Funded
2. **Executed Capital Calls** - Full history including newly approved calls
3. **Audit Log** - All processed calls with validation results

## Implementation

### 1. Add export function to `database.py`

```python
def export_commitment_tracker_df() -> pd.DataFrame:
    """Return commitment tracker as a formatted DataFrame for Excel export."""
    # Query from DB, format amounts as numbers (not strings), add % Funded column
    
def export_audit_log_df() -> pd.DataFrame:
    """Return processed calls as a formatted DataFrame for Excel export."""
    # Include: timestamp, fund, amount, status, action, reviewer, commitment msg, wire msg
```

### 2. Add download buttons to `app.py`

On the Dashboard page, after each table, add:
```python
import io

def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

st.download_button(
    "Download Excel",
    data=to_excel_bytes(df),
    file_name=f"commitment_tracker_{datetime.now().strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
```

Also add a "Full Report" download on the Dashboard that combines all three sheets into one Excel workbook.

### 3. On the Audit Log page

Add a download button that exports all processed calls.

## Acceptance Criteria

- [ ] Commitment Tracker downloads with formatted EUR amounts and % Funded
- [ ] Executed Calls downloads with all historical records
- [ ] Audit Log downloads with all processed calls and validation details
- [ ] "Full Report" button creates a multi-sheet Excel workbook
- [ ] Filenames include the current date (e.g., `sentinel_report_20260413.xlsx`)
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `app.py` (add download buttons)
- `database.py` (add export functions)

## Do NOT

- Change the database schema
- Modify the validation engine
- Add new pip dependencies (openpyxl is already installed)
