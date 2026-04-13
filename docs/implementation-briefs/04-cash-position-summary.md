# Brief 04: Cash Position Summary

## Priority: WAVE 1 | Parallel-Safe | No Dependencies

## Context

Treasury needs to know the total EUR required across all pending capital calls, broken down by due date, to ensure sufficient liquidity. Currently there's no aggregated view of upcoming cash outflows.

## What to Build

A "Cash Position" section on the Dashboard that shows:
1. **Total pending outflow** across all upcoming calls
2. **Breakdown by due date** (timeline view)
3. **Breakdown by vintage/investor** (who owes what)
4. **A simple timeline chart** showing cumulative cash needed over time

## Implementation

### 1. Cash position KPI cards

Add a new section on the Dashboard between the charts and the tables:
```python
st.markdown('<div class="section-header">Cash Position - Upcoming Outflows</div>', unsafe_allow_html=True)

total_pending = upcoming["Amount"].sum()
calls_count = len(upcoming)

c1, c2, c3 = st.columns(3)
c1.markdown(f'''<div class="kpi-card">
    <div class="kpi-label">Total Pending Outflow</div>
    <div class="kpi-value">EUR {total_pending/1e6:,.1f}M</div>
    <div class="kpi-sub">{calls_count} capital calls</div>
</div>''', unsafe_allow_html=True)
```

### 2. Timeline chart

Create a bar chart showing amounts grouped by due date:
```python
import plotly.express as px

# Group upcoming calls by due date
timeline = upcoming.groupby("Due Date")["Amount"].sum().reset_index()
timeline.columns = ["Due Date", "Amount"]
timeline = timeline.sort_values("Due Date")

fig = px.bar(timeline, x="Due Date", y="Amount",
             title="", color_discrete_sequence=["#F97316"],
             labels={"Amount": "EUR"})
fig.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=40),
                  plot_bgcolor="white" if not dark else "#1E293B",
                  paper_bgcolor="white" if not dark else "#1E293B",
                  font_color="#1E293B" if not dark else "#F1F5F9")
st.plotly_chart(fig, use_container_width=True)
```

### 3. Breakdown by investor

Show a small table:
```python
by_investor = upcoming.groupby("Investor")["Amount"].agg(["sum", "count"]).reset_index()
by_investor.columns = ["Investor", "Total Amount", "# Calls"]
by_investor["Total Amount"] = by_investor["Total Amount"].apply(lambda x: f"EUR {x:,.0f}")
st.dataframe(by_investor, use_container_width=True, hide_index=True)
```

## Acceptance Criteria

- [ ] Total pending outflow KPI card shows aggregated EUR amount
- [ ] Bar chart shows amounts by due date
- [ ] Breakdown table shows amounts by investor/vintage
- [ ] All amounts are formatted as EUR with thousands separators
- [ ] Works in both light and dark mode (chart backgrounds adapt)
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `app.py` (Dashboard page only)

## Do NOT

- Change the database schema
- Add new pages
- Modify any other files
