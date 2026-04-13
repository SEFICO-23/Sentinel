# Brief 10: Dashboard Date Range & Vintage Filters

## Priority: WAVE 2 | Parallel-Safe | Depends on Wave 1 merge

## Context

The Dashboard currently shows all-time data with no filtering. Users need to filter by vintage year and view commitment changes over specific time periods.

## What to Build

1. **Vintage filter** dropdown to show only funds from a specific vintage (2010, 2015, 2019)
2. **Charts update** based on selected vintage
3. **KPI cards update** to reflect filtered data
4. **"All Vintages" option** as default

## Implementation

### 1. Add filter controls at top of Dashboard

```python
if page == "Dashboard":
    st.markdown("## Commitment Tracker Dashboard")
    
    # Filter row
    filter_col1, filter_col2 = st.columns([1, 3])
    with filter_col1:
        vintage_options = ["All Vintages"] + sorted(ct["Investor"].unique().tolist())
        selected_vintage = st.selectbox("Filter by Vintage", vintage_options)
    
    # Apply filter
    if selected_vintage != "All Vintages":
        ct_filtered = ct[ct["Investor"] == selected_vintage]
    else:
        ct_filtered = ct
```

### 2. Use `ct_filtered` for all KPI cards and charts

Replace all references to `ct` in the Dashboard page with `ct_filtered`. The KPIs, bar chart, pie chart, and tables should all reflect the filter.

### 3. Show filter context

When a filter is active, display it:
```python
if selected_vintage != "All Vintages":
    st.caption(f"Showing data for: {selected_vintage} ({len(ct_filtered)} funds)")
```

## Acceptance Criteria

- [ ] Vintage dropdown with "All Vintages" default
- [ ] KPI cards update when vintage is selected
- [ ] Charts update when vintage is selected
- [ ] Tables update when vintage is selected
- [ ] "All Vintages" shows complete data (same as current behavior)
- [ ] Filter context shown when active
- [ ] Works in both light and dark mode
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `app.py` (Dashboard page only)

## Do NOT

- Change the database schema
- Modify any other pages
- Add complex date range filtering (that's for the Audit Log in Brief 09)
