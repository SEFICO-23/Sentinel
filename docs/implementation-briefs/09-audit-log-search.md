# Brief 09: Audit Log Search & Filter

## Priority: WAVE 2 | Parallel-Safe | Depends on Wave 1 merge

## Context

The Audit Log page currently shows all processed calls in a flat list. As the volume grows, users need to filter by fund, date range, status, and reviewer. This is also important for regulatory audits.

## What to Build

1. **Filter controls** at the top of the Audit Log page
2. **Date range picker** for time-based filtering
3. **Multi-select filters** for status, fund, and reviewer
4. **Result count** showing how many records match
5. **Pagination** or virtual scrolling for large result sets

## Implementation

### 1. Filter UI

At the top of the Audit Log page:
```python
st.markdown("## Audit Log")

# Filter row
f1, f2, f3, f4 = st.columns(4)
with f1:
    date_range = st.date_input("Date Range", value=(datetime(2026, 1, 1), datetime.now()), 
                                format="DD.MM.YYYY")
with f2:
    status_filter = st.multiselect("Status", ["EXECUTED", "REJECTED", "ESCALATED"], default=[])
with f3:
    fund_filter = st.multiselect("Fund", get_unique_funds(), default=[])
with f4:
    reviewer_filter = st.multiselect("Reviewer", get_unique_reviewers(), default=[])
```

### 2. Database query with filters

Add a filtered query function to `database.py`:
```python
def get_processed_calls_filtered(
    date_from=None, date_to=None,
    statuses=None, funds=None, reviewer=None
) -> list[dict]:
    query = "SELECT * FROM processed_calls WHERE 1=1"
    params = []
    if date_from:
        query += " AND processed_at >= ?"
        params.append(date_from.isoformat())
    if date_to:
        query += " AND processed_at <= ?"
        params.append(date_to.isoformat() + "T23:59:59")
    if statuses:
        placeholders = ",".join("?" * len(statuses))
        query += f" AND action IN ({placeholders})"
        params.extend(statuses)
    if funds:
        placeholders = ",".join("?" * len(funds))
        query += f" AND (fund_name_matched IN ({placeholders}) OR fund_name_extracted IN ({placeholders}))"
        params.extend(funds)
        params.extend(funds)
    if reviewer:
        placeholders = ",".join("?" * len(reviewer))
        query += f" AND reviewer IN ({placeholders})"
        params.extend(reviewer)
    query += " ORDER BY processed_at DESC"
    ...
```

### 3. Helper functions

```python
def get_unique_funds() -> list[str]:
    """Get distinct fund names from processed_calls for filter dropdown."""
    
def get_unique_reviewers() -> list[str]:
    """Get distinct reviewer names from processed_calls for filter dropdown."""
```

### 4. Result count and summary

```python
filtered = db.get_processed_calls_filtered(...)
st.caption(f"Showing {len(filtered)} of {total_count} records")
```

### 5. Pagination

For large result sets, add simple pagination:
```python
PAGE_SIZE = 20
total_pages = (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE
page_num = st.number_input("Page", min_value=1, max_value=max(1, total_pages), value=1)
page_data = filtered[(page_num-1)*PAGE_SIZE : page_num*PAGE_SIZE]
```

## Acceptance Criteria

- [ ] Date range filter works correctly
- [ ] Multi-select status filter (EXECUTED/REJECTED/ESCALATED)
- [ ] Multi-select fund filter
- [ ] Multi-select reviewer filter
- [ ] Filters can be combined (AND logic)
- [ ] Result count shown
- [ ] Pagination for large result sets
- [ ] "Clear Filters" button resets all filters
- [ ] Existing audit log display (expandable details) still works
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `database.py` (filtered query, helper functions)
- `app.py` (Audit Log page)

## Do NOT

- Change the `processed_calls` schema
- Remove the existing audit log card display
