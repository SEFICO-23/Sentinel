"""
Project Sentinel - Treasury Operations Automation
Capital Call Processing Dashboard with AI-Driven Validation

Production-ready version with:
- SQLite persistence (survives browser refresh)
- LLM-powered PDF extraction (Claude API + regex fallback)
- Role-based 4-eye reviewer validation
"""
import base64
import html as html_mod
import io
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from data_loader import (
    load_commitment_tracker,
    load_upcoming_calls,
    load_executed_calls,
    load_approved_wires,
)
from llm_extractor import extract_smart, check_api_available
from validation_engine import run_full_validation
from email_sender import send_confirmation_email, validate_email
import database as db


def esc(text) -> str:
    """Escape user/PDF-sourced strings before embedding in unsafe_allow_html blocks."""
    return html_mod.escape(str(text)) if text else ""


# ─────────────────────────────────────────────
# Database Initialization
# ─────────────────────────────────────────────
db.init_db()
db.seed_default_users()
db.seed_from_excel(load_commitment_tracker(), load_executed_calls())
db.seed_wires_from_excel(load_approved_wires())
db.seed_gp_contacts()
db.seed_distributions_and_nav()


# ─────────────────────────────────────────────
# Page Config & Theme
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Project Sentinel | Treasury Ops",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Theme state
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

dark = st.session_state.dark_mode

# CSS with theme variables
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {{
    --bg-primary: {'#0F172A' if dark else '#FFFFFF'};
    --bg-secondary: {'#1E293B' if dark else '#F8FAFC'};
    --bg-card: {'#1E293B' if dark else '#FFFFFF'};
    --border: {'#334155' if dark else '#E2E8F0'};
    --text-primary: {'#F1F5F9' if dark else '#1E293B'};
    --text-secondary: {'#94A3B8' if dark else '#475569'};
    --text-muted: {'#64748B' if dark else '#64748B'};
    --accent: #2563EB;
    --shadow: {'rgba(0,0,0,0.3)' if dark else 'rgba(0,0,0,0.06)'};
    --shadow-hover: {'rgba(0,0,0,0.5)' if dark else 'rgba(0,0,0,0.1)'};
}}

.stApp {{ font-family: 'Inter', sans-serif; {'background-color: #0F172A;' if dark else ''} }}
.block-container {{ padding-top: 1.5rem; max-width: 1400px; }}

/* Streamlit dark mode overrides */
{'''
/* === GLOBAL DARK OVERRIDES === */

/* Main app background */
.stApp, [data-testid="stAppViewContainer"], .main .block-container { background-color: #0F172A !important; }

/* Sidebar */
section[data-testid="stSidebar"] { background-color: #1E293B !important; }
section[data-testid="stSidebar"] * { color: #F1F5F9; }
section[data-testid="stSidebar"] .stMarkdown { color: #F1F5F9; }
section[data-testid="stSidebar"] label { color: #94A3B8 !important; }
section[data-testid="stSidebar"] .stDivider { border-color: #334155 !important; }

/* All text */
h1, h2, h3, h4, h5, h6 { color: #F1F5F9 !important; }
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span, .stCaption, .stText { color: #CBD5E1 !important; }
label, .stSelectbox label, .stTextInput label, .stTextArea label, .stNumberInput label,
.stRadio label, .stCheckbox label, .stToggle label, .stDateInput label { color: #94A3B8 !important; }

/* Metrics */
div[data-testid="stMetric"] label { color: #94A3B8 !important; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #F1F5F9 !important; }
div[data-testid="stMetricDelta"] { color: #94A3B8 !important; }

/* Inputs and selects */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
.stSelectbox > div > div, .stMultiSelect > div > div,
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
    background-color: #0F172A !important; color: #F1F5F9 !important;
    border-color: #334155 !important;
}
div[data-baseweb="select"] > div { background-color: #0F172A !important; color: #F1F5F9 !important; border-color: #334155 !important; }
div[data-baseweb="popover"] > div { background-color: #1E293B !important; }
div[data-baseweb="menu"] { background-color: #1E293B !important; }
div[data-baseweb="menu"] li { color: #F1F5F9 !important; }
div[data-baseweb="menu"] li:hover { background-color: #334155 !important; }

/* Date input */
div[data-baseweb="calendar"] { background-color: #1E293B !important; color: #F1F5F9 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background-color: #1E293B !important; border-bottom-color: #334155 !important; }
.stTabs [data-baseweb="tab"] { color: #94A3B8 !important; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: #F1F5F9 !important; }
.stTabs [data-baseweb="tab-panel"] { background-color: #0F172A !important; }

/* Expanders */
div[data-testid="stExpander"] { border-color: #334155 !important; background-color: #1E293B !important; }
div[data-testid="stExpander"] summary { color: #F1F5F9 !important; }
div[data-testid="stExpander"] details > div { color: #CBD5E1 !important; }

/* DataFrames / Tables */
.stDataFrame, div[data-testid="stDataFrame"] { background-color: #1E293B !important; }
div[data-testid="stDataFrame"] th { background-color: #0F172A !important; color: #F1F5F9 !important; }
div[data-testid="stDataFrame"] td { color: #CBD5E1 !important; background-color: #1E293B !important; }
div[data-testid="stDataFrame"] [data-testid="glideDataEditor"] { background-color: #1E293B !important; }

/* Buttons */
.stButton > button[kind="secondary"] { background-color: #1E293B !important; color: #F1F5F9 !important; border-color: #334155 !important; }
.stButton > button[kind="secondary"]:hover { background-color: #334155 !important; }
.stDownloadButton > button { background-color: #1E293B !important; color: #F1F5F9 !important; border-color: #334155 !important; }
.stDownloadButton > button:hover { background-color: #334155 !important; }

/* Alerts */
div[data-testid="stAlert"] { border-color: #334155 !important; }
.stAlert > div { background-color: #1E293B !important; }

/* Radio buttons */
.stRadio > div { color: #F1F5F9 !important; }
.stRadio label span { color: #F1F5F9 !important; }

/* Toggle */
.stToggle label span { color: #F1F5F9 !important; }

/* File uploader */
div[data-testid="stFileUploader"] { background-color: #1E293B !important; border-color: #334155 !important; }
div[data-testid="stFileUploader"] label { color: #94A3B8 !important; }
div[data-testid="stFileUploader"] span { color: #CBD5E1 !important; }
div[data-testid="stFileUploader"] button { background-color: #334155 !important; color: #F1F5F9 !important; }

/* Dividers */
hr, .stDivider { border-color: #334155 !important; }

/* Progress bar */
.stProgress > div > div { background-color: #334155 !important; }

/* Pagination / number input */
.stNumberInput button { background-color: #334155 !important; color: #F1F5F9 !important; }

/* Multiselect tags */
span[data-baseweb="tag"] { background-color: #334155 !important; color: #F1F5F9 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #0F172A; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }

/* HTML tables (urgency table etc.) */
table { color: #CBD5E1 !important; }
table th { background-color: #1E293B !important; color: #F1F5F9 !important; border-color: #334155 !important; }
table td { background-color: #0F172A !important; color: #CBD5E1 !important; border-color: #334155 !important; }

''' if dark else ''}

.kpi-card {{
    background: var(--bg-card); border-radius: 12px; padding: 1.25rem 1.5rem;
    border: 1px solid var(--border); box-shadow: 0 1px 3px var(--shadow);
    transition: box-shadow 0.2s ease;
}}
.kpi-card:hover {{ box-shadow: 0 4px 12px var(--shadow-hover); }}
.kpi-label {{ font-size: 0.8rem; color: var(--text-secondary); font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; }}
.kpi-value {{ font-size: 1.75rem; font-weight: 700; color: var(--text-primary); line-height: 1.2; }}
.kpi-sub {{ font-size: 0.78rem; color: var(--text-secondary); margin-top: 0.25rem; }}

.badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }}
.badge-pass {{ background: {'#052E16' if dark else '#DCFCE7'}; color: {'#4ADE80' if dark else '#166534'}; }}
.badge-fail {{ background: {'#450A0A' if dark else '#FEE2E2'}; color: {'#FCA5A5' if dark else '#991B1B'}; }}
.badge-warn {{ background: {'#451A03' if dark else '#FEF3C7'}; color: {'#FCD34D' if dark else '#92400E'}; }}
.badge-info {{ background: {'#172554' if dark else '#DBEAFE'}; color: {'#60A5FA' if dark else '#1E40AF'}; }}
.badge-pending {{ background: {'#3B0764' if dark else '#F3E8FF'}; color: {'#C084FC' if dark else '#6B21A8'}; }}

.val-card {{
    background: var(--bg-card); border-radius: 12px; padding: 1.5rem;
    border-left: 4px solid; margin-bottom: 1rem; box-shadow: 0 1px 3px var(--shadow);
}}
.val-card p {{ color: var(--text-secondary) !important; }}
.val-card h4 {{ color: var(--text-primary) !important; }}
.val-pass {{ border-color: #22C55E; }}
.val-fail {{ border-color: #EF4444; }}

.section-header {{
    font-size: 1.1rem; font-weight: 600; color: var(--text-primary);
    margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--border);
}}

.email-template {{
    background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px;
    padding: 1.5rem; font-size: 0.9rem; line-height: 1.6; color: var(--text-secondary);
}}

.upload-zone {{
    border: 2px dashed {'#475569' if dark else '#CBD5E1'}; border-radius: 12px; padding: 2rem;
    text-align: center; background: var(--bg-secondary); transition: border-color 0.2s;
}}
.upload-zone:hover {{ border-color: #2563EB; }}
.upload-zone p {{ color: var(--text-secondary) !important; }}

.method-badge {{
    display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px;
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
}}
.method-regex {{ background: {'#172554' if dark else '#DBEAFE'}; color: {'#60A5FA' if dark else '#1E40AF'}; }}
.method-llm {{ background: {'#3B0764' if dark else '#F3E8FF'}; color: {'#C084FC' if dark else '#6B21A8'}; }}
.method-both {{ background: {'#451A03' if dark else '#FEF3C7'}; color: {'#FCD34D' if dark else '#92400E'}; }}

#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Load Data (from DB + Excel for upcoming)
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_upcoming_calls():
    return load_upcoming_calls()

def get_wires_dataframe():
    return db.get_approved_wires_df()

def get_ct_dataframe():
    rows = db.get_commitment_tracker()
    return pd.DataFrame(rows).rename(columns={
        "investor": "Investor", "fund_name": "Fund Name",
        "total_commitment": "Total Commitment", "total_funded_ytd": "Total Funded YTD",
        "remaining_open_commitment": "Remaining Open Commitment",
    })

def get_exec_dataframe():
    rows = db.get_executed_calls()
    return pd.DataFrame(rows).rename(columns={
        "investor": "Investor", "fund_name": "Fund Name",
        "amount": "Capital Call Amount Paid", "value_date": "Value Date",
    })

upcoming = get_upcoming_calls()
wires = get_wires_dataframe()
ct = get_ct_dataframe()
executed = get_exec_dataframe()


# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────
def _generate_email(validation: dict, reviewer_name: str) -> str:
    fund = esc(validation["fund_name_matched"])
    amount = validation["amount"]
    due = esc(validation["due_date"])
    reviewer_safe = esc(reviewer_name)
    now = datetime.now().strftime("%d.%m.%Y")
    return f"""<strong>Subject:</strong> Payment Confirmation - Capital Call - {fund}<br><br>
Dear Counterparty,<br><br>
We hereby confirm that the following capital call payment has been processed:<br><br>
&nbsp;&nbsp;&nbsp;&nbsp;<strong>Fund:</strong> {fund}<br>
&nbsp;&nbsp;&nbsp;&nbsp;<strong>Amount:</strong> EUR {amount:,.2f}<br>
&nbsp;&nbsp;&nbsp;&nbsp;<strong>Value Date:</strong> {now}<br>
&nbsp;&nbsp;&nbsp;&nbsp;<strong>Due Date per Notice:</strong> {due}<br>
&nbsp;&nbsp;&nbsp;&nbsp;<strong>Reference:</strong> Capital Call - {fund} - {now}<br><br>
Payment has been initiated via wire transfer to the account specified in your notice.
Please allow 1-2 business days for settlement.<br><br>
Should you require any further information, please do not hesitate to contact us.<br><br>
Kind regards,<br>
Treasury Operations<br>
<em>Approved by: {reviewer_safe}</em><br>
<em>Processed via Project Sentinel</em>"""


def parse_due_date(date_str):
    """Parse DD.MM.YYYY date string (or pandas Timestamp) to datetime."""
    if isinstance(date_str, datetime):
        return date_str
    try:
        return datetime.strptime(str(date_str).strip(), "%d.%m.%Y")
    except (ValueError, AttributeError):
        return None


def days_until(date_str):
    """Return the number of days until a due date (negative if overdue)."""
    due = parse_due_date(date_str)
    if due is None:
        return None
    return (due - datetime.now()).days


def urgency_badge(days):
    """Return (label, css_class) for a given number of days until due."""
    if days is None:
        return "unknown", "badge-info"
    if days < 0:
        return f"OVERDUE ({abs(days)}d)", "badge-fail"
    if days <= 3:
        return f"URGENT ({days}d)", "badge-fail"
    if days <= 7:
        return f"SOON ({days}d)", "badge-warn"
    return f"{days} days", "badge-pass"


def display_pdf(file_bytes: bytes):
    """Render a PDF in the browser using a base64-encoded iframe."""
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    pdf_display = (
        '<iframe src="data:application/pdf;base64,' + b64 + '" '
        'width="100%" height="600" '
        'style="border: 1px solid var(--border); border-radius: 8px;">'
        '</iframe>'
    )
    st.markdown(pdf_display, unsafe_allow_html=True)


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    """Convert a DataFrame to Excel bytes for st.download_button."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


def to_multi_sheet_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    """Convert multiple DataFrames to a multi-sheet Excel workbook."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    title_color = "#F1F5F9" if dark else "#1E293B"
    sub_color = "#94A3B8" if dark else "#475569"
    st.markdown(f"""
    <div style="padding: 1rem 0;">
        <h1 style="font-size: 1.4rem; font-weight: 700; color: {title_color}; margin: 0;">
            <span style="color: #2563EB;" aria-hidden="true">&#9632;</span> Project Sentinel
        </h1>
        <p style="font-size: 0.8rem; color: {sub_color}; margin: 0.25rem 0 0 0;">Treasury Operations Automation</p>
    </div>
    """, unsafe_allow_html=True)

    # Dark/Light mode toggle
    mode_label = "Light Mode" if dark else "Dark Mode"
    if st.toggle("Dark Mode", value=st.session_state.dark_mode, key="theme_toggle"):
        if not st.session_state.dark_mode:
            st.session_state.dark_mode = True
            st.rerun()
    else:
        if st.session_state.dark_mode:
            st.session_state.dark_mode = False
            st.rerun()

    st.divider()

    # User selector (simulates login)
    users = db.get_users()
    user_options = {u["display_name"]: u for u in users}
    selected_user_name = st.selectbox(
        "Logged in as",
        options=list(user_options.keys()),
        index=0,
    )
    current_user = user_options[selected_user_name]
    role_colors = {"admin": "badge-info", "reviewer": "badge-pass", "analyst": "badge-pending"}
    st.markdown(
        f'<span class="badge {role_colors.get(current_user["role"], "badge-info")}">'
        f'{current_user["role"].upper()}</span>',
        unsafe_allow_html=True,
    )
    st.divider()

    # Pending amendments badge
    pending_amendments_count = len(db.get_pending_amendments())
    amendments_label = "Amendments"
    if pending_amendments_count > 0:
        amendments_label = f"Amendments ({pending_amendments_count})"

    page = st.radio(
        "Navigation",
        ["Dashboard", "Process Capital Call", amendments_label, "Approved Wire Instructions", "GP Contacts", "Audit Log"],
        label_visibility="collapsed",
    )

    # LLM settings
    st.divider()
    st.markdown("**AI Extraction**")
    api_key = st.text_input("Claude API Key (optional)", type="password",
                            value=st.session_state.get("api_key", ""),
                            help="Enables LLM-powered extraction for complex PDFs")
    if api_key:
        st.session_state.api_key = api_key
    llm_available = check_api_available(api_key or st.session_state.get("api_key"))
    if llm_available:
        st.markdown('<span class="badge badge-pass">LLM Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-warn">Regex Only</span>', unsafe_allow_html=True)

    # Email / SMTP settings
    st.divider()
    with st.expander("Email Settings"):
        smtp_server = st.text_input("SMTP Server", value=st.session_state.get("smtp_server", "smtp.office365.com"), key="smtp_server_input")
        smtp_port = st.number_input("Port", value=st.session_state.get("smtp_port", 587), min_value=1, max_value=65535, key="smtp_port_input")
        smtp_user = st.text_input("Email", placeholder="treasury@company.com", value=st.session_state.get("smtp_user", ""), key="smtp_user_input")
        smtp_pass = st.text_input("Password", type="password", value=st.session_state.get("smtp_pass", ""), key="smtp_pass_input")

        # Persist in session state
        st.session_state.smtp_server = smtp_server
        st.session_state.smtp_port = int(smtp_port)
        st.session_state.smtp_user = smtp_user
        st.session_state.smtp_pass = smtp_pass

    smtp_configured = all([
        st.session_state.get("smtp_server"),
        st.session_state.get("smtp_port"),
        st.session_state.get("smtp_user"),
        st.session_state.get("smtp_pass"),
    ])
    if smtp_configured:
        st.markdown('<span class="badge badge-pass">SMTP Configured</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-warn">SMTP Not Set</span>', unsafe_allow_html=True)

    st.divider()
    st.caption(f"Last refreshed: {datetime.now().strftime('%d.%m.%Y %H:%M')}")


# ═════════════════════════════════════════════
# PAGE: DASHBOARD
# ═════════════════════════════════════════════
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

    if selected_vintage != "All Vintages":
        st.caption(f"Showing data for: {selected_vintage} ({len(ct_filtered)} funds)")

    # Due-date alert banner
    if not upcoming.empty and "Due Date" in upcoming.columns:
        _urgent = upcoming["Due Date"].apply(days_until)
        _urgent_mask = _urgent.apply(lambda d: d is not None and d <= 3)
        _urgent_count = int(_urgent_mask.sum())
        if _urgent_count > 0:
            st.error(
                f"**{_urgent_count} capital call(s) due within 3 days!** "
                "Review the Upcoming Calls tab immediately."
            )

    total_commitment = ct_filtered["Total Commitment"].sum()
    total_funded = ct_filtered["Total Funded YTD"].sum()
    total_remaining = ct_filtered["Remaining Open Commitment"].sum()
    num_funds = len(ct_filtered)
    pct_deployed = (total_funded / total_commitment * 100) if total_commitment else 0
    pending_calls = len(upcoming)
    executed_count = len(db.get_processed_calls())

    k1, k2, k3, k4, k5 = st.columns(5)
    for col, label, value, sub in [
        (k1, "Total Commitments", f"EUR {total_commitment/1e6:,.1f}M", f"{num_funds} funds"),
        (k2, "Total Funded YTD", f"EUR {total_funded/1e6:,.1f}M", f"{pct_deployed:.1f}% deployed"),
        (k3, "Remaining Open", f"EUR {total_remaining/1e6:,.1f}M", "across all funds"),
        (k4, "Pending Calls", str(pending_calls), "awaiting processing"),
        (k5, "Processed (Total)", str(executed_count), "all-time records"),
    ]:
        col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # Charts
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown('<div class="section-header">Commitment by Fund</div>', unsafe_allow_html=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Funded", x=ct_filtered["Fund Name"], y=ct_filtered["Total Funded YTD"],
            marker_color="#2563EB", hovertemplate="EUR %{y:,.0f}<extra>Funded</extra>"
        ))
        fig_bar.add_trace(go.Bar(
            name="Remaining", x=ct_filtered["Fund Name"], y=ct_filtered["Remaining Open Commitment"],
            marker_color="#93C5FD", hovertemplate="EUR %{y:,.0f}<extra>Remaining</extra>"
        ))
        chart_bg = "#1E293B" if dark else "white"
        chart_paper = "#0F172A" if dark else "white"
        chart_font = "#F1F5F9" if dark else "#1E293B"
        chart_grid = "#334155" if dark else "#E2E8F0"
        fig_bar.update_layout(
            barmode="stack", height=380,
            margin=dict(l=20, r=20, t=10, b=100),
            legend=dict(orientation="h", y=1.08, font=dict(color=chart_font)),
            xaxis=dict(tickangle=-45, tickfont=dict(size=10, color=chart_font), gridcolor=chart_grid),
            yaxis=dict(title="EUR", tickformat=",.0s", tickfont=dict(color=chart_font), title_font=dict(color=chart_font), gridcolor=chart_grid),
            plot_bgcolor=chart_bg, paper_bgcolor=chart_paper, font=dict(color=chart_font),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with ch2:
        st.markdown('<div class="section-header">Allocation by Vintage</div>', unsafe_allow_html=True)
        vintage_agg = ct_filtered.groupby("Investor")["Total Commitment"].sum().reset_index()
        vintage_agg.columns = ["Vintage", "Total"]
        fig_pie = px.pie(
            vintage_agg, values="Total", names="Vintage",
            color_discrete_sequence=["#2563EB", "#3B82F6", "#93C5FD"],
            hole=0.45,
        )
        fig_pie.update_traces(textinfo="label+percent", hovertemplate="%{label}<br>EUR %{value:,.0f}<extra></extra>")
        fig_pie.update_layout(height=380, margin=dict(l=20, r=20, t=10, b=20), showlegend=False,
                              paper_bgcolor=chart_paper, font=dict(color=chart_font))
        st.plotly_chart(fig_pie, use_container_width=True)


    # ── Cash Position - Upcoming Outflows ──
    st.markdown('<div class="section-header">Cash Position - Upcoming Outflows</div>', unsafe_allow_html=True)

    if upcoming.empty:
        st.info("No upcoming capital calls to display.")
    else:
        total_pending = upcoming["Amount"].sum()
        calls_count = len(upcoming)
        nearest_due = upcoming["Due Date"].min()

        cp1, cp2, cp3 = st.columns(3)
        cp1.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Total Pending Outflow</div>
            <div class="kpi-value">EUR {total_pending/1e6:,.1f}M</div>
            <div class="kpi-sub">{calls_count} capital calls</div>
        </div>''', unsafe_allow_html=True)
        cp2.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Average Call Size</div>
            <div class="kpi-value">EUR {total_pending/calls_count/1e6:,.1f}M</div>
            <div class="kpi-sub">per capital call</div>
        </div>''', unsafe_allow_html=True)
        cp3.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Nearest Due Date</div>
            <div class="kpi-value">{pd.Timestamp(nearest_due).strftime("%d %b %Y") if pd.notna(nearest_due) else "N/A"}</div>
            <div class="kpi-sub">earliest upcoming call</div>
        </div>''', unsafe_allow_html=True)

        st.markdown("")

        cp_ch1, cp_ch2 = st.columns(2)
        with cp_ch1:
            timeline = upcoming.groupby("Due Date")["Amount"].sum().reset_index()
            timeline.columns = ["Due Date", "Amount"]
            timeline = timeline.sort_values("Due Date")

            fig_timeline = px.bar(
                timeline, x="Due Date", y="Amount",
                title="", color_discrete_sequence=["#F97316"],
                labels={"Amount": "EUR"},
            )
            fig_timeline.update_layout(
                height=280,
                margin=dict(l=20, r=20, t=10, b=40),
                plot_bgcolor="#1E293B" if dark else "white",
                paper_bgcolor="#0F172A" if dark else "white",
                font=dict(color="#F1F5F9" if dark else "#1E293B"),
                yaxis=dict(tickformat=",.0s", gridcolor="#334155" if dark else "#E2E8F0"),
                xaxis=dict(gridcolor="#334155" if dark else "#E2E8F0"),
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

        with cp_ch2:
            by_investor = upcoming.groupby("Investor")["Amount"].agg(["sum", "count"]).reset_index()
            by_investor.columns = ["Investor", "Total Amount", "# Calls"]
            by_investor = by_investor.sort_values("Total Amount", ascending=False)
            by_investor["Total Amount"] = by_investor["Total Amount"].apply(lambda x: f"EUR {x:,.0f}")
            st.dataframe(by_investor, use_container_width=True, hide_index=True)

    st.markdown("")

    # Tables in tabs
    tab_tracker, tab_upcoming, tab_executed, tab_portfolio = st.tabs(["Commitment Tracker", "Upcoming Calls", "Executed Calls", "Portfolio Summary"])

    with tab_tracker:
        display_ct = ct_filtered.copy()
        for c in ["Total Commitment", "Total Funded YTD", "Remaining Open Commitment"]:
            display_ct[c] = display_ct[c].apply(lambda x: f"EUR {x:,.0f}")
        display_ct["% Funded"] = ct_filtered.apply(
            lambda r: f"{r['Total Funded YTD']/r['Total Commitment']*100:.1f}%" if r['Total Commitment'] > 0 else "0%",
            axis=1
        )
        st.dataframe(display_ct, use_container_width=True, hide_index=True, height=480)
        ct_export = db.export_commitment_tracker_df()
        st.download_button(
            "📥 Download Excel",
            data=to_excel_bytes(ct_export, "Commitment Tracker"),
            file_name=f"commitment_tracker_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with tab_upcoming:
        if upcoming.empty:
            st.info("No upcoming capital calls.")
        else:
            display_up = upcoming.copy()
            display_up["Amount"] = display_up["Amount"].apply(lambda x: f"EUR {x:,.0f}")
            display_up["Days Until Due"] = upcoming["Due Date"].apply(days_until)
            display_up["Urgency"] = display_up["Days Until Due"].apply(
                lambda d: urgency_badge(d)[0]
            )
            # Render with color-coded badges via HTML
            rows_html = ""
            for _, row in display_up.iterrows():
                days_val = row["Days Until Due"]
                label, badge_cls = urgency_badge(days_val)
                days_display = str(days_val) if days_val is not None else "–"
                rows_html += (
                    f"<tr style='border-bottom:1px solid var(--border);'>"
                    f"<td style='padding:0.5rem;'>{esc(row['Investor'])}</td>"
                    f"<td style='padding:0.5rem;'>{esc(row['Fund Name'])}</td>"
                    f"<td style='padding:0.5rem;'>{esc(row['Amount'])}</td>"
                    f"<td style='padding:0.5rem;'>{esc(str(row['Due Date']))}</td>"
                    f"<td style='padding:0.5rem; text-align:center;'>{esc(days_display)}</td>"
                    f'<td style="padding:0.5rem;"><span class="badge {badge_cls}">{esc(label)}</span></td>'
                    f"</tr>"
                )
            st.markdown(f"""
            <table style="width:100%; border-collapse:collapse; font-size:0.9rem;">
                <thead>
                    <tr style="border-bottom:2px solid var(--border); text-align:left;">
                        <th style="padding:0.5rem; color:var(--text-secondary);">Investor</th>
                        <th style="padding:0.5rem; color:var(--text-secondary);">Fund Name</th>
                        <th style="padding:0.5rem; color:var(--text-secondary);">Amount</th>
                        <th style="padding:0.5rem; color:var(--text-secondary);">Due Date</th>
                        <th style="padding:0.5rem; color:var(--text-secondary); text-align:center;">Days Until Due</th>
                        <th style="padding:0.5rem; color:var(--text-secondary);">Urgency</th>
                    </tr>
                </thead>
                <tbody style="color:var(--text-primary);">
                    {rows_html}
                </tbody>
            </table>
            """, unsafe_allow_html=True)

    with tab_executed:
        if executed.empty:
            st.info("No executed capital calls recorded.")
        else:
            display_exec = executed.copy()
            display_exec["Capital Call Amount Paid"] = display_exec["Capital Call Amount Paid"].apply(
                lambda x: f"EUR {x:,.0f}" if pd.notna(x) else ""
            )
            st.dataframe(display_exec, use_container_width=True, hide_index=True, height=400)
            exec_export = db.export_executed_calls_df()
            st.download_button(
                "📥 Download Excel",
                data=to_excel_bytes(exec_export, "Executed Calls"),
                file_name=f"executed_calls_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with tab_portfolio:
        summary = db.get_portfolio_summary()
        if not summary:
            st.info("No portfolio data available yet.")
        else:
            # Portfolio-level KPIs
            total_called_all = sum(s["total_called"] for s in summary)
            total_dist_all = sum(s["total_distributed"] for s in summary)
            total_nav_all = sum(s["latest_nav"] for s in summary)
            portfolio_dpi = total_dist_all / total_called_all if total_called_all > 0 else 0
            portfolio_tvpi = (total_dist_all + total_nav_all) / total_called_all if total_called_all > 0 else 0

            pk1, pk2, pk3, pk4 = st.columns(4)
            for col, label, value, sub in [
                (pk1, "Total Called", f"EUR {total_called_all/1e6:,.1f}M", "capital deployed"),
                (pk2, "Total Distributed", f"EUR {total_dist_all/1e6:,.1f}M", "cash returned"),
                (pk3, "Portfolio DPI", f"{portfolio_dpi:.2f}x", "distributions / paid-in"),
                (pk4, "Portfolio TVPI", f"{portfolio_tvpi:.2f}x", "(distributions + NAV) / paid-in"),
            ]:
                col.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("")

            # Per-fund metrics table
            st.markdown('<div class="section-header">Fund Performance Metrics</div>', unsafe_allow_html=True)
            summary_df = pd.DataFrame(summary)
            display_summary = pd.DataFrame({
                "Investor": summary_df["investor"],
                "Fund": summary_df["fund_name"],
                "Total Called": summary_df["total_called"].apply(lambda x: f"EUR {x:,.0f}"),
                "Total Distributed": summary_df["total_distributed"].apply(lambda x: f"EUR {x:,.0f}"),
                "Latest NAV": summary_df["latest_nav"].apply(lambda x: f"EUR {x:,.0f}"),
                "Net Cash Flow": summary_df["net_cash_flow"].apply(lambda x: f"EUR {x:,.0f}"),
                "DPI": summary_df["dpi"].apply(lambda x: f"{x:.2f}x"),
                "TVPI": summary_df["tvpi"].apply(lambda x: f"{x:.2f}x"),
            })
            st.dataframe(display_summary, use_container_width=True, hide_index=True, height=480)

            # Net Cash Flow chart
            st.markdown("")
            st.markdown('<div class="section-header">Cumulative Cash Flows Over Time</div>', unsafe_allow_html=True)
            cash_flows = db.get_cumulative_cash_flows()
            if cash_flows:
                cf_df = pd.DataFrame(cash_flows)
                fig_cf = go.Figure()
                fig_cf.add_trace(go.Scatter(
                    x=cf_df["date"], y=cf_df["cumulative_calls"],
                    name="Cumulative Calls (Out)",
                    line=dict(color="#EF4444", width=2),
                    hovertemplate="EUR %{y:,.0f}<extra>Calls</extra>",
                ))
                fig_cf.add_trace(go.Scatter(
                    x=cf_df["date"], y=cf_df["cumulative_distributions"],
                    name="Cumulative Distributions (In)",
                    line=dict(color="#22C55E", width=2),
                    hovertemplate="EUR %{y:,.0f}<extra>Distributions</extra>",
                ))
                fig_cf.add_trace(go.Scatter(
                    x=cf_df["date"], y=cf_df["net_cash_flow"],
                    name="Net Cash Flow",
                    line=dict(color="#2563EB", width=2, dash="dash"),
                    hovertemplate="EUR %{y:,.0f}<extra>Net</extra>",
                ))
                cf_bg = "#1E293B" if dark else "white"
                cf_paper = "#0F172A" if dark else "white"
                cf_font = "#F1F5F9" if dark else "#1E293B"
                cf_grid = "#334155" if dark else "#E2E8F0"
                fig_cf.update_layout(
                    height=400,
                    margin=dict(l=20, r=20, t=10, b=40),
                    legend=dict(orientation="h", y=1.08, font=dict(color=cf_font)),
                    yaxis=dict(title="EUR", tickformat=",.0s", gridcolor=cf_grid, tickfont=dict(color=cf_font), title_font=dict(color=cf_font)),
                    xaxis=dict(title="Date", gridcolor=cf_grid, tickfont=dict(color=cf_font), title_font=dict(color=cf_font)),
                    plot_bgcolor=cf_bg, paper_bgcolor=cf_paper, font=dict(color=cf_font),
                )
                st.plotly_chart(fig_cf, use_container_width=True)
            else:
                st.info("No cash flow data available for charting.")

            # Distribution entry form
            st.markdown("")
            with st.expander("Record Distribution"):
                fund_names = sorted(ct["Fund Name"].unique().tolist())
                dist_fund = st.selectbox("Fund", fund_names, key="dist_fund")
                dist_amount = st.number_input("Amount (EUR)", min_value=0.0, step=10000.0, key="dist_amount")
                dist_type_map = {
                    "Return of Capital": "return_of_capital",
                    "Income": "income",
                    "Gain": "gain",
                    "Other": "other",
                }
                dist_type_label = st.selectbox("Type", list(dist_type_map.keys()), key="dist_type")
                dist_date = st.date_input("Value Date", key="dist_date")
                dist_notes = st.text_input("Notes (optional)", key="dist_notes")

                if st.button("Record Distribution", type="primary"):
                    if dist_amount <= 0:
                        st.error("Amount must be greater than zero.")
                    else:
                        fund_row = ct[ct["Fund Name"] == dist_fund]
                        investor_name = fund_row["Investor"].iloc[0] if not fund_row.empty else ""
                        db.add_distribution(
                            investor=investor_name,
                            fund_name=dist_fund,
                            amount=dist_amount,
                            distribution_type=dist_type_map[dist_type_label],
                            value_date=dist_date.strftime("%Y-%m-%d"),
                            notes=dist_notes,
                        )
                        st.success(f"Distribution of EUR {dist_amount:,.0f} recorded for {dist_fund}.")
                        st.rerun()

            # NAV entry form
            with st.expander("Record NAV"):
                nav_fund_names = sorted(ct["Fund Name"].unique().tolist())
                nav_fund = st.selectbox("Fund", nav_fund_names, key="nav_fund")
                nav_amount = st.number_input("NAV Amount (EUR)", min_value=0.0, step=100000.0, key="nav_amount")
                nav_date = st.date_input("Reporting Date", key="nav_date")
                nav_source = st.selectbox("Source", ["manual", "administrator", "audit"], key="nav_source")

                if st.button("Record NAV", type="primary"):
                    if nav_amount <= 0:
                        st.error("NAV amount must be greater than zero.")
                    else:
                        db.add_nav_record(
                            fund_name=nav_fund,
                            nav_amount=nav_amount,
                            reporting_date=nav_date.strftime("%Y-%m-%d"),
                            source=nav_source,
                        )
                        st.success(f"NAV of EUR {nav_amount:,.0f} recorded for {nav_fund}.")
                        st.rerun()

    # Full Report download (all sheets combined)
    st.divider()
    today_str = datetime.now().strftime('%Y%m%d')
    full_report_sheets = {
        "Commitment Tracker": db.export_commitment_tracker_df(),
        "Executed Calls": db.export_executed_calls_df(),
        "Audit Log": db.export_audit_log_df(),
    }
    st.download_button(
        "📥 Download Full Report (All Sheets)",
        data=to_multi_sheet_excel_bytes(full_report_sheets),
        file_name=f"sentinel_report_{today_str}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


# ═════════════════════════════════════════════
# PAGE: PROCESS CAPITAL CALL
# ═════════════════════════════════════════════
elif page == "Process Capital Call":
    st.markdown("## Process Capital Call Notice")
    st.markdown("Upload one or more PDF capital call notices to extract, validate, and approve.")

    if "confirm_execution" not in st.session_state:
        st.session_state.confirm_execution = False
    if "batch_results" not in st.session_state:
        st.session_state.batch_results = None
    if "confirm_batch_execution" not in st.session_state:
        st.session_state.confirm_batch_execution = False

    # Upload
    st.markdown("""
    <div class="upload-zone">
        <p style="font-size: 1.1rem; font-weight: 600; color: #475569; margin-bottom: 0.25rem;">
            Drop your capital call PDF(s) here
        </p>
        <p style="font-size: 0.85rem; color: #475569;">
            Supports single or batch upload &mdash; PDF notices from any GP counterparty
        </p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload PDF Notices",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    # ── BATCH PROCESSING (2+ files) ──────────────
    if uploaded_files and len(uploaded_files) > 1:
        st.divider()
        st.markdown("### Batch Processing Results")

        # Process all files (cached in session state keyed by filenames)
        current_names = tuple(sorted(f.name for f in uploaded_files))
        cached = st.session_state.batch_results
        if cached is None or cached.get("_file_key") != current_names:
            results = []
            skipped = []
            progress = st.progress(0)
            api_key = st.session_state.get("api_key", "")
            for i, file in enumerate(uploaded_files):
                if db.is_file_already_processed(file.name):
                    skipped.append(file.name)
                    progress.progress((i + 1) / len(uploaded_files))
                    continue
                try:
                    batch_file_bytes = file.read()
                    extracted = extract_smart(file_bytes=batch_file_bytes, filename=file.name, api_key=api_key)
                    validation = run_full_validation(extracted, ct, wires)
                    batch_archive_path = db.archive_pdf(batch_file_bytes, file.name)
                    results.append({"filename": file.name, "validation": validation, "extracted": extracted,
                                    "archive_path": batch_archive_path})
                except Exception as e:
                    results.append({
                        "filename": file.name,
                        "validation": {
                            "fund_name_matched": None, "fund_name_extracted": "PARSE ERROR",
                            "amount": 0, "commitment_check": {"passed": False},
                            "wire_check": {"passed": False}, "overall_status": f"ERROR: {e}",
                        },
                        "extracted": None,
                        "error": str(e),
                    })
                progress.progress((i + 1) / len(uploaded_files))
            progress.empty()
            st.session_state.batch_results = {"_file_key": current_names, "results": results, "skipped": skipped}

        results = st.session_state.batch_results["results"]
        skipped = st.session_state.batch_results["skipped"]

        # Show skipped files
        if skipped:
            st.info(f"**{len(skipped)} file(s) already processed** and skipped: {', '.join(esc(s) for s in skipped)}")

        if not results:
            st.success("All uploaded files have already been processed.")
            st.stop()

        # Summary table
        summary_df = pd.DataFrame([{
            "File": r["filename"],
            "Fund": r["validation"].get("fund_name_matched") or r["validation"].get("fund_name_extracted", "N/A"),
            "Amount": f"EUR {r['validation']['amount']:,.0f}" if r["validation"]["amount"] else "N/A",
            "Commitment": "PASS" if r["validation"]["commitment_check"]["passed"] else "FAIL",
            "Wire": "PASS" if r["validation"]["wire_check"]["passed"] else "FAIL",
            "Status": r["validation"]["overall_status"],
        } for r in results])

        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        # Counts
        approved = [r for r in results if r["validation"]["overall_status"] == "APPROVED"]
        rejected = [r for r in results if r["validation"]["overall_status"] != "APPROVED"]
        m1, m2 = st.columns(2)
        m1.metric("Ready to Approve", len(approved))
        m2.metric("Rejected / Needs Review", len(rejected))

        # Expandable detail per file
        for r in results:
            v = r["validation"]
            status_label = v["overall_status"]
            with st.expander(f"{esc(r['filename'])} — {esc(status_label)}"):
                if r.get("error"):
                    st.error(f"Parse error: {esc(r['error'])}")
                    continue
                d1, d2, d3 = st.columns(3)
                d1.metric("Fund", v.get("fund_name_extracted", "N/A"))
                d2.metric("Amount", f"EUR {v['amount']:,.0f}")
                d3.metric("Due Date", v.get("due_date", "N/A"))

                cc = v["commitment_check"]
                wc = v["wire_check"]
                vc1, vc2 = st.columns(2)
                vc1.markdown(f"**Commitment Check:** {'PASS' if cc['passed'] else 'FAIL'}")
                if cc.get("message"):
                    vc1.caption(cc["message"])
                vc2.markdown(f"**Wire Check:** {'PASS' if wc['passed'] else 'FAIL'}")
                if wc.get("message"):
                    vc2.caption(wc["message"])

        # Bulk approval workflow
        if approved:
            st.divider()
            st.markdown('<div class="section-header">Bulk Approval (4-Eye Check)</div>', unsafe_allow_html=True)
            st.info(f"{len(approved)} call(s) passed all checks. Select a reviewer to approve them all at once.")

            reviewers = db.get_reviewers()
            reviewer_options = [r for r in reviewers if r["username"] != current_user["username"]]

            if not reviewer_options:
                st.warning("No eligible reviewers available. The 4-eye principle requires a second authorized person.")
                st.stop()

            if current_user["role"] == "analyst":
                st.caption("As an analyst, you can submit for review but cannot self-approve.")

            reviewer_names = [f"{r['display_name']} ({r['role']})" for r in reviewer_options]
            selected_reviewer_idx = st.selectbox("Select Reviewer (2nd pair of eyes)",
                                                  range(len(reviewer_names)),
                                                  format_func=lambda i: reviewer_names[i],
                                                  key="batch_reviewer")
            selected_reviewer = reviewer_options[selected_reviewer_idx]
            review_notes = st.text_area("Review Notes (optional)", placeholder="Any observations...",
                                        height=80, key="batch_notes")

            if not st.session_state.confirm_batch_execution:
                if st.button("Approve All Passing Calls", type="primary", use_container_width=True):
                    st.session_state.confirm_batch_execution = True
                    st.rerun()
            else:
                st.warning(
                    f"**Confirm batch execution of {len(approved)} capital call(s)?**\n\n"
                    f"Total: EUR {sum(r['validation']['amount'] for r in approved):,.0f}\n\n"
                    f"Submitter: {esc(current_user['display_name'])} | "
                    f"Reviewer: {esc(selected_reviewer['display_name'])}"
                )
                bc1, bc2 = st.columns(2)
                if bc1.button("Yes, Execute All", type="primary", use_container_width=True):
                    exec_count = 0
                    for r in approved:
                        email_body = _generate_email(r["validation"], selected_reviewer["display_name"])
                        db.execute_capital_call(
                            validation=r["validation"],
                            reviewer_username=selected_reviewer["username"],
                            review_notes=review_notes,
                            filename=r["filename"],
                            email_body=email_body,
                            archive_path=r.get("archive_path"),
                        )
                        exec_count += 1
                    st.session_state.confirm_batch_execution = False
                    st.session_state.batch_results = None
                    st.success(f"Successfully executed {exec_count} capital call(s).")
                    st.rerun()

                if bc2.button("Cancel", use_container_width=True, key="batch_cancel"):
                    st.session_state.confirm_batch_execution = False
                    st.rerun()

    # ── SINGLE FILE PROCESSING (existing flow) ──
    elif uploaded_files and len(uploaded_files) == 1:
        uploaded = uploaded_files[0]
        # Clear batch state
        st.session_state.batch_results = None
        st.session_state.confirm_batch_execution = False

        # Check if already processed in DB
        if db.is_file_already_processed(uploaded.name):
            last_exec = st.session_state.pop("last_executed_call", None)
            if last_exec:
                st.success(f"Capital call for **{esc(last_exec['fund'])}** executed and persisted to database.")
                st.markdown('<div class="section-header">Send Confirmation Email</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="email-template">{last_exec["email_body"]}</div>', unsafe_allow_html=True)
                st.markdown("")
                recipient = st.text_input("Recipient Email", placeholder="gp-ops@fundmanager.com", key="post_exec_recipient")
                send_disabled = not (recipient and validate_email(recipient) and smtp_configured)
                ec1, ec2 = st.columns(2)
                with ec1:
                    if st.button("Send Email", type="primary", use_container_width=True, disabled=send_disabled):
                        success, message = send_confirmation_email(
                            smtp_server=st.session_state.smtp_server,
                            smtp_port=st.session_state.smtp_port,
                            smtp_user=st.session_state.smtp_user,
                            smtp_password=st.session_state.smtp_pass,
                            to_email=recipient,
                            subject=f"Payment Confirmation - Capital Call - {last_exec['fund']}",
                            html_body=last_exec["email_body"],
                        )
                        if success:
                            db.update_email_status(last_exec["call_id"], recipient)
                            st.success(message)
                        else:
                            st.error(message)
                with ec2:
                    st.download_button(
                        "Download Email as HTML",
                        data=last_exec["email_body"],
                        file_name=f"confirmation_{last_exec['fund'].replace(' ', '_')}.html",
                        mime="text/html",
                        use_container_width=True,
                    )
                if not smtp_configured:
                    st.caption("Configure SMTP settings in the sidebar to enable email sending.")
                if recipient and not validate_email(recipient):
                    st.warning("Please enter a valid email address.")
            else:
                st.success(f"**{esc(uploaded.name)}** has already been executed. Check the Audit Log for details.")
            st.stop()

        st.divider()

        # Read file bytes once upfront (UploadedFile.read() exhausts the buffer)
        file_bytes = uploaded.read()

        # Extract
        try:
            with st.spinner("Extracting data from PDF..."):
                api_key = st.session_state.get("api_key", "")
                extracted = extract_smart(file_bytes=file_bytes, filename=uploaded.name, api_key=api_key)
        except Exception as e:
            st.error(f"Failed to parse PDF: {e}. Please ensure the file is a valid, unencrypted capital call notice.")
            st.stop()

        if extracted["amount"] <= 0:
            st.error("Could not extract a valid amount from this PDF. Manual processing required.")
            st.stop()

        # Validate
        with st.spinner("Running validation checks..."):
            validation = run_full_validation(extracted, ct, wires)

        # Archive the original PDF
        archive_path = db.archive_pdf(file_bytes, uploaded.name)

        # Two-column layout: PDF preview | Extracted data
        col_pdf, col_data = st.columns([1, 1])

        with col_pdf:
            st.markdown('<div class="section-header">Original Notice</div>', unsafe_allow_html=True)
            with st.expander("View Original PDF", expanded=True):
                display_pdf(file_bytes)

        with col_data:
            st.markdown('<div class="section-header">1. Extracted Data</div>', unsafe_allow_html=True)

            # Show extraction method
            method = extracted.get("extraction_method", "regex")
            confidence = extracted.get("extraction_confidence", "high")
            method_class = {"regex": "method-regex", "llm": "method-llm", "regex+llm": "method-both"}
            st.markdown(
                f'Extraction: <span class="method-badge {method_class.get(method, "method-regex")}">{method}</span> '
                f'&nbsp; Confidence: <span class="badge {"badge-pass" if confidence == "high" else "badge-warn"}">{confidence}</span>',
                unsafe_allow_html=True,
            )

            e1, e2, e3 = st.columns(3)
            e1.metric("Fund Name", validation["fund_name_extracted"])
            e2.metric("Amount", f"EUR {validation['amount']:,.0f}")
            e3.metric("Due Date", validation["due_date"])

            e4, e5, e6 = st.columns(3)
            e4.metric("Investor", validation["investor"])
            e5.metric("Currency", validation["currency"])
            if validation["fund_name_matched"]:
                e6.metric("Matched To", f"{validation['fund_name_matched']} ({validation['fund_match_score']:.0f}%)")
            else:
                e6.metric("Matched To", "NO MATCH FOUND")

        st.divider()

        # ── Duplicate Detection ──
        duplicates_found = False
        exact_dupes = []
        fuzzy_dupes = []
        if validation["fund_name_matched"]:
            exact_dupes = db.find_potential_duplicates(
                validation["fund_name_matched"], validation["amount"], validation["due_date"]
            )
            fuzzy_dupes = db.find_fuzzy_duplicates(
                validation["fund_name_matched"], validation["amount"]
            )

            if exact_dupes:
                duplicates_found = True
                st.error(f"**DUPLICATE DETECTED:** An identical capital call (same fund, amount, due date) "
                         f"was already processed on {exact_dupes[0]['processed_at']} "
                         f"(file: {exact_dupes[0]['filename']}, status: {exact_dupes[0]['action']})")
            elif fuzzy_dupes:
                duplicates_found = True
                st.warning(f"**Potential duplicate:** A similar call for {esc(validation['fund_name_matched'])} "
                           f"with EUR {fuzzy_dupes[0]['amount']:,.0f} was processed on "
                           f"{fuzzy_dupes[0]['processed_at']}. Verify this is not a re-submission.")

        if duplicates_found:
            override_reason = st.text_input("Override reason (required to proceed)",
                                            placeholder="e.g., Corrected notice, supersedes previous...",
                                            key="duplicate_override_reason")
        else:
            override_reason = None

        # Validation Results
        st.markdown('<div class="section-header">2. Validation Results</div>', unsafe_allow_html=True)

        v1, v2 = st.columns(2)
        cc = validation["commitment_check"]
        with v1:
            badge_class = "val-pass" if cc["passed"] else "val-fail"
            icon = "&#10003;" if cc["passed"] else "&#10007;"
            st.markdown(f"""
            <div class="val-card {badge_class}">
                <h4 style="margin:0 0 0.5rem 0;">{icon} Commitment Check</h4>
                <p style="margin:0; font-size: 0.9rem; color: #475569;">{esc(cc['message'])}</p>
            </div>
            """, unsafe_allow_html=True)
            if not cc["passed"] and "overage" in cc:
                st.error(f"Overage: EUR {cc['overage']:,.0f} above the remaining commitment limit.")

        wc = validation["wire_check"]
        with v2:
            badge_class = "val-pass" if wc["passed"] else "val-fail"
            icon = "&#10003;" if wc["passed"] else "&#10007;"
            st.markdown(f"""
            <div class="val-card {badge_class}">
                <h4 style="margin:0 0 0.5rem 0;">{icon} Wire Verification</h4>
                <p style="margin:0; font-size: 0.9rem; color: #475569;">{esc(wc['message'])}</p>
            </div>
            """, unsafe_allow_html=True)
            if not wc["passed"]:
                st.error("SECURITY ALERT: Wire instructions do not match approved records. Do not proceed.")

        # Overall Status
        st.divider()
        status = validation["overall_status"]
        if status == "APPROVED":
            status_badge = '<span class="badge badge-pass">APPROVED</span>'
        elif "WIRE" in status:
            status_badge = '<span class="badge badge-fail">REJECTED - WIRE MISMATCH</span>'
        elif "COMMITMENT" in status:
            status_badge = '<span class="badge badge-warn">REJECTED - OVER COMMITMENT</span>'
        else:
            status_badge = f'<span class="badge badge-fail">{esc(status)}</span>'

        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <p style="font-size: 0.85rem; color: #475569; margin-bottom: 0.5rem;">OVERALL STATUS</p>
            <div style="font-size: 1.2rem;">{status_badge}</div>
        </div>
        """, unsafe_allow_html=True)

        # GP Contact for Escalation (shown on validation failure)
        if not cc["passed"] or not wc["passed"]:
            contacts = db.get_contacts_for_fund(validation["fund_name_matched"]) if validation["fund_name_matched"] else []
            if contacts:
                st.markdown('<div class="section-header">GP Contact for Escalation</div>', unsafe_allow_html=True)
                for contact in contacts:
                    primary = " (Primary)" if contact["primary_contact"] else ""
                    st.markdown(f"""
                    <div class="kpi-card" style="margin-bottom: 0.5rem;">
                        <strong>{esc(contact['contact_name'])}</strong>{primary}<br>
                        <span style="color: var(--text-secondary);">{esc(contact['role'])}</span><br>
                        Email: {esc(contact['email'])} | Phone: {esc(contact['phone'])}
                    </div>
                    """, unsafe_allow_html=True)

        # 4-Eye Approval Workflow
        st.divider()
        st.markdown('<div class="section-header">3. Approval Workflow (4-Eye Check)</div>', unsafe_allow_html=True)

        if status == "APPROVED":
            st.info("This call has passed all automated checks. A second reviewer must confirm before execution.")

            # Reviewer must be a different person with reviewer/admin role
            reviewers = db.get_reviewers()
            reviewer_options = [r for r in reviewers if r["username"] != current_user["username"]]

            if not reviewer_options:
                st.warning("No eligible reviewers available. The 4-eye principle requires a second authorized person.")
                st.stop()

            if current_user["role"] == "analyst":
                st.caption("As an analyst, you can submit for review but cannot self-approve.")

            reviewer_names = [f"{r['display_name']} ({r['role']})" for r in reviewer_options]
            selected_reviewer_idx = st.selectbox("Select Reviewer (2nd pair of eyes)", range(len(reviewer_names)),
                                                  format_func=lambda i: reviewer_names[i])
            selected_reviewer = reviewer_options[selected_reviewer_idx]
            review_notes = st.text_area("Review Notes (optional)", placeholder="Any observations...", height=80)

            # Block approval if duplicate detected without override reason
            duplicate_blocked = duplicates_found and not (override_reason and override_reason.strip())
            if duplicate_blocked:
                st.warning("A duplicate was detected. Provide an override reason above to proceed.")

            # Prepend override reason to review notes for audit trail
            final_review_notes = review_notes
            if duplicates_found and override_reason and override_reason.strip():
                final_review_notes = f"[DUPLICATE OVERRIDE: {override_reason.strip()}] {review_notes}"

            col_approve, col_reject = st.columns(2)
            with col_approve:
                if not st.session_state.confirm_execution:
                    if st.button("Confirm & Execute", type="primary", use_container_width=True,
                                 disabled=duplicate_blocked):
                        st.session_state.confirm_execution = True
                        st.rerun()
                else:
                    matched = validation["fund_name_matched"]
                    st.warning(
                        f"**Confirm execution of EUR {validation['amount']:,.0f} "
                        f"to {esc(matched)}?**\n\n"
                        f"Submitter: {esc(current_user['display_name'])} | "
                        f"Reviewer: {esc(selected_reviewer['display_name'])}"
                    )
                    c1, c2 = st.columns(2)
                    if c1.button("Yes, Execute Now", type="primary", use_container_width=True):
                        email_body = _generate_email(validation, selected_reviewer["display_name"])
                        call_id = db.execute_capital_call(
                            validation=validation,
                            reviewer_username=selected_reviewer["username"],
                            review_notes=final_review_notes,
                            filename=uploaded.name,
                            email_body=email_body,
                            archive_path=archive_path,
                        )
                        st.session_state.confirm_execution = False
                        st.session_state.last_executed_call = {
                            "call_id": call_id,
                            "fund": matched,
                            "email_body": email_body,
                        }
                        st.rerun()

                    if c2.button("Cancel", use_container_width=True):
                        st.session_state.confirm_execution = False
                        st.rerun()

            with col_reject:
                if st.button("Reject & Flag", type="secondary", use_container_width=True):
                    db.log_rejection(
                        validation=validation,
                        reviewer_username=selected_reviewer["username"],
                        review_notes=final_review_notes,
                        filename=uploaded.name,
                        archive_path=archive_path,
                    )
                    st.session_state.confirm_execution = False
                    st.warning("Call rejected and logged to audit trail.")
        else:
            st.warning(
                f"This capital call cannot be auto-approved due to: **{status}**. "
                "Manual review and escalation required."
            )
            # Amendment request form when capital call exceeds commitment
            if "COMMITMENT" in status and validation.get("fund_name_matched"):
                matched_fund = validation["fund_name_matched"]
                fund_info = db.get_commitment_for_fund(matched_fund)
                overage = cc.get("overage", 0)

                if fund_info and overage > 0:
                    st.warning(f"Amount exceeds remaining commitment by EUR {overage:,.0f}")

                    with st.expander("Request Commitment Increase"):
                        st.markdown("Submit a commitment increase to resolve this capital call.")
                        increase_amount = st.number_input(
                            "Increase Amount (EUR)",
                            min_value=int(overage),
                            value=int(overage),
                            step=100000,
                            key="single_amendment_increase",
                        )
                        amendment_reason = st.text_area(
                            "Justification",
                            placeholder="e.g., Side letter amendment, GP notification of increased allocation...",
                            key="single_amendment_reason",
                        )
                        if st.button("Submit Amendment Request", key="single_amendment_submit"):
                            if not amendment_reason.strip():
                                st.error("A justification is required for amendment requests.")
                            else:
                                db.create_commitment_amendment(
                                    fund_name=matched_fund,
                                    current_commitment=fund_info["total_commitment"],
                                    current_remaining=fund_info["remaining_open_commitment"],
                                    requested_increase=increase_amount,
                                    reason=amendment_reason,
                                    capital_call_filename=uploaded.name,
                                    requested_by=current_user["username"],
                                )
                                st.success("Amendment request submitted for review.")

            if st.button("Acknowledge & Log for Escalation"):
                db.log_escalation(validation=validation, filename=uploaded.name, archive_path=archive_path)
                st.info("Logged for escalation. Senior treasury officer will be notified.")


# ═════════════════════════════════════════════
# PAGE: APPROVED WIRE INSTRUCTIONS
# ═════════════════════════════════════════════
elif page.startswith("Amendments"):
    st.markdown("## Commitment Amendments")

    # Tabs: Pending Review | Amendment History
    tab_pending, tab_history = st.tabs(["Pending Review", "Amendment History"])

    with tab_pending:
        pending = db.get_pending_amendments()
        if not pending:
            st.info("No pending amendment requests.")
        else:
            st.markdown(f"**{len(pending)} amendment(s) awaiting review**")

            for amendment in pending:
                with st.expander(
                    f"{esc(amendment['fund_name'])} — EUR {amendment['requested_increase']:,.0f} increase "
                    f"(requested by {esc(amendment['requested_by'])})"
                ):
                    a1, a2, a3 = st.columns(3)
                    a1.metric("Current Commitment", f"EUR {amendment['current_commitment']:,.0f}")
                    a2.metric("Requested Increase", f"EUR {amendment['requested_increase']:,.0f}")
                    a3.metric("New Commitment", f"EUR {amendment['new_commitment']:,.0f}")

                    st.markdown(f"**Current Remaining:** EUR {amendment['current_remaining']:,.0f}")
                    st.markdown(f"**Justification:** {esc(amendment['reason'])}")
                    if amendment.get("capital_call_filename"):
                        st.caption(f"Related file: {esc(amendment['capital_call_filename'])}")
                    st.caption(f"Submitted: {esc(amendment['created_at'])}")

                    # 4-eye: requester cannot approve own amendment
                    if current_user["role"] in ("reviewer", "admin"):
                        if current_user["username"] == amendment["requested_by"]:
                            st.warning("You cannot review your own amendment request (4-eye principle).")
                        else:
                            review_notes = st.text_area(
                                "Review Notes",
                                placeholder="Optional notes...",
                                key=f"amend_notes_{amendment['id']}",
                            )
                            ac1, ac2 = st.columns(2)
                            if ac1.button("Approve", type="primary", key=f"amend_approve_{amendment['id']}",
                                          use_container_width=True):
                                db.approve_commitment_amendment(
                                    amendment_id=amendment["id"],
                                    reviewed_by=current_user["username"],
                                    notes=review_notes,
                                )
                                st.success(
                                    f"Amendment approved. {esc(amendment['fund_name'])} commitment "
                                    f"increased by EUR {amendment['requested_increase']:,.0f}."
                                )
                                st.rerun()
                            if ac2.button("Reject", key=f"amend_reject_{amendment['id']}",
                                          use_container_width=True):
                                db.reject_commitment_amendment(
                                    amendment_id=amendment["id"],
                                    reviewed_by=current_user["username"],
                                    notes=review_notes,
                                )
                                st.warning("Amendment rejected.")
                                st.rerun()
                    else:
                        st.info("Only reviewers and admins can approve or reject amendments.")

    with tab_history:
        history = db.get_amendment_history()
        if not history:
            st.info("No amendment history yet.")
        else:
            for h in history:
                if h["status"] == "APPROVED":
                    badge = '<span class="badge badge-pass">APPROVED</span>'
                elif h["status"] == "REJECTED":
                    badge = '<span class="badge badge-fail">REJECTED</span>'
                else:
                    badge = '<span class="badge badge-pending">PENDING</span>'

                st.markdown(f"""
                <div class="kpi-card" style="margin-bottom: 1rem;">
                    <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;">
                        <div><strong>{esc(h['fund_name'])}</strong> &nbsp; {badge}</div>
                        <span style="font-size: 0.8rem; color: #475569;">{esc(h['created_at'])}</span>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.85rem; color: #475569;">
                        Increase: EUR {h['requested_increase']:,.0f} |
                        New Commitment: EUR {h['new_commitment']:,.0f} |
                        Requested by: {esc(h['requested_by'])} |
                        Reviewed by: {esc(h.get('reviewed_by') or 'N/A')}
                    </div>
                    <div style="margin-top: 0.25rem; font-size: 0.82rem; color: #64748B;">
                        Reason: {esc(h['reason'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)


elif page == "Approved Wire Instructions":
    st.markdown("## Approved Wire Instructions Database")
    st.markdown("Reference list of verified counterparty banking details for wire transfers.")

    # Current wires table (from DB)
    wires_list = db.get_approved_wires()
    wires_display = get_wires_dataframe()
    st.dataframe(
        wires_display, use_container_width=True, hide_index=True,
        column_config={
            "Fund Name": st.column_config.TextColumn("Fund Name", width="large"),
            "Beneficiary Bank": st.column_config.TextColumn("Bank", width="medium"),
            "Swift/BIC": st.column_config.TextColumn("SWIFT/BIC", width="small"),
            "IBAN / Account Number": st.column_config.TextColumn("IBAN / Account No.", width="large"),
            "Currency": st.column_config.TextColumn("CCY", width="small"),
        },
    )

    # ── Propose Change form ──
    with st.expander("Propose Wire Instruction Change"):
        if not wires_list:
            st.warning("No wire instructions available.")
        else:
            fund_options = {w["fund_name"]: w for w in wires_list}
            wire_to_change = st.selectbox("Fund", list(fund_options.keys()), key="wire_change_fund")
            selected_wire = fund_options[wire_to_change]

            field_labels = {
                "beneficiary_bank": "Beneficiary Bank",
                "swift_bic": "SWIFT/BIC",
                "iban": "IBAN / Account Number",
            }
            field = st.selectbox("Field to Change", list(field_labels.keys()),
                                 format_func=lambda f: field_labels[f], key="wire_change_field")

            current_value = selected_wire.get(field, "")
            st.caption(f"Current value: **{esc(current_value)}**")

            new_value = st.text_input("New Value", key="wire_change_new_val")
            reason = st.text_area("Reason for Change (required)", key="wire_change_reason")

            if st.button("Submit Change Request", key="wire_change_submit"):
                if not new_value.strip():
                    st.error("New value cannot be empty.")
                elif not reason.strip():
                    st.error("A reason is required for audit purposes.")
                elif new_value.strip() == str(current_value).strip():
                    st.error("New value is the same as the current value.")
                else:
                    db.create_wire_change_request(
                        wire_id=selected_wire["id"],
                        field=field,
                        old_val=str(current_value),
                        new_val=new_value.strip(),
                        reason=reason.strip(),
                        requested_by=current_user["username"],
                    )
                    st.success("Change request submitted for review.")
                    st.rerun()

    # ── Pending changes (reviewers/admins only) ──
    if current_user["role"] in ("reviewer", "admin"):
        pending = db.get_pending_wire_changes()
        if pending:
            st.markdown("### Pending Wire Change Requests")
            for change in pending:
                with st.container():
                    st.markdown(
                        f"**{esc(change['fund_name'])}** — Change `{esc(change['field_changed'])}` "
                        f"from `{esc(change['old_value'])}` to `{esc(change['new_value'])}`"
                    )
                    st.caption(
                        f"Reason: {esc(change['reason'])} | "
                        f"Requested by: {esc(change['requested_by'])} | "
                        f"Submitted: {esc(change['created_at'])}"
                    )

                    # 4-eye: cannot review own request
                    if change["requested_by"] == current_user["username"]:
                        st.info("You cannot review your own change request (4-eye principle).")
                    else:
                        c1, c2 = st.columns(2)
                        review_notes = st.text_input(
                            "Review notes (optional)",
                            key=f"wire_review_notes_{change['id']}",
                        )
                        with c1:
                            if st.button("Approve", key=f"wire_approve_{change['id']}", type="primary"):
                                try:
                                    db.approve_wire_change(
                                        change['id'], current_user["username"], review_notes
                                    )
                                    st.success("Change approved and applied.")
                                    st.rerun()
                                except ValueError as e:
                                    st.error(str(e))
                        with c2:
                            if st.button("Reject", key=f"wire_reject_{change['id']}"):
                                try:
                                    db.reject_wire_change(
                                        change['id'], current_user["username"], review_notes
                                    )
                                    st.warning("Change request rejected.")
                                    st.rerun()
                                except ValueError as e:
                                    st.error(str(e))
                    st.divider()

    # ── Change history ──
    with st.expander("Wire Change History"):
        history = db.get_wire_change_history()
        if not history:
            st.info("No wire change requests have been submitted yet.")
        else:
            history_df = pd.DataFrame(history)
            history_df = history_df.rename(columns={
                "fund_name": "Fund", "field_changed": "Field",
                "old_value": "Old Value", "new_value": "New Value",
                "reason": "Reason", "requested_by": "Requested By",
                "reviewed_by": "Reviewed By", "status": "Status",
                "review_notes": "Review Notes",
                "created_at": "Submitted", "reviewed_at": "Reviewed At",
            })
            display_cols = ["Fund", "Field", "Old Value", "New Value", "Reason",
                            "Requested By", "Reviewed By", "Status", "Review Notes",
                            "Submitted", "Reviewed At"]
            st.dataframe(
                history_df[display_cols], use_container_width=True, hide_index=True,
            )

    st.info("Wire instructions are maintained by the compliance team. All changes require dual-authorization.")


# ═════════════════════════════════════════════
# PAGE: GP CONTACTS
# ═════════════════════════════════════════════
elif page == "GP Contacts":
    st.markdown("## GP Contact Directory")
    st.markdown("Manage GP operations contacts for escalation when capital calls fail validation.")

    tab_directory, tab_add = st.tabs(["Contact Directory", "Add Contact"])

    with tab_directory:
        all_contacts = db.get_all_contacts()
        if not all_contacts:
            st.info("No contacts in the directory yet. Use the 'Add Contact' tab to create one.")
        else:
            # Search / filter
            search_query = st.text_input("Search by fund name", placeholder="Type to filter...", key="contact_search")

            # Group contacts by fund
            funds_seen = []
            grouped = {}
            for c in all_contacts:
                fn = c["fund_name"]
                if fn not in grouped:
                    grouped[fn] = []
                    funds_seen.append(fn)
                grouped[fn].append(c)

            displayed = 0
            for fund in funds_seen:
                if search_query and search_query.lower() not in fund.lower():
                    continue
                displayed += 1
                contacts_list = grouped[fund]
                with st.expander(f"{esc(fund)} ({len(contacts_list)} contact{'s' if len(contacts_list) != 1 else ''})"):
                    for c in contacts_list:
                        inactive_tag = ' <span class="badge badge-warn">INACTIVE</span>' if not c["active"] else ""
                        primary_tag = ' <span class="badge badge-pass">PRIMARY</span>' if c["primary_contact"] else ""
                        st.markdown(f"""
                        <div class="kpi-card" style="margin-bottom: 0.75rem;">
                            <strong>{esc(c['contact_name'])}</strong>{primary_tag}{inactive_tag}<br>
                            <span style="color: var(--text-secondary);">{esc(c['role'])}</span><br>
                            Email: {esc(c['email'])} | Phone: {esc(c['phone'])}
                            {'<br><em style="color: var(--text-muted);">' + esc(c["notes"]) + '</em>' if c.get("notes") else ""}
                        </div>
                        """, unsafe_allow_html=True)

                        # Edit / Deactivate controls
                        ec1, ec2, ec3 = st.columns([2, 1, 1])
                        with ec2:
                            if c["active"] and not c["primary_contact"]:
                                if st.button("Set Primary", key=f"primary_{c['id']}", use_container_width=True):
                                    # Unset other primaries for this fund
                                    for other in contacts_list:
                                        if other["primary_contact"]:
                                            db.update_contact(other["id"], primary_contact=0)
                                    db.update_contact(c["id"], primary_contact=1)
                                    st.rerun()
                        with ec3:
                            if c["active"]:
                                if st.button("Deactivate", key=f"deactivate_{c['id']}", use_container_width=True):
                                    db.deactivate_contact(c["id"])
                                    st.success(f"Deactivated {esc(c['contact_name'])}.")
                                    st.rerun()

            if displayed == 0 and search_query:
                st.info(f"No contacts found matching '{esc(search_query)}'.")

    with tab_add:
        st.markdown("### Add New Contact")
        with st.form("add_contact_form"):
            # Fund name - allow picking existing or typing new
            existing_funds = sorted(set(c["fund_name"] for c in db.get_all_contacts()))
            ct_funds = sorted(set(r["fund_name"] for r in db.get_commitment_tracker()))
            all_fund_options = sorted(set(existing_funds + ct_funds))

            new_fund = st.selectbox("Fund Name", options=["(Type new fund name)"] + all_fund_options, key="new_contact_fund")
            custom_fund = ""
            if new_fund == "(Type new fund name)":
                custom_fund = st.text_input("Enter fund name", key="new_contact_custom_fund")

            new_name = st.text_input("Contact Name", key="new_contact_name")
            new_role = st.text_input("Role", value="Operations", key="new_contact_role")
            new_email = st.text_input("Email", key="new_contact_email")
            new_phone = st.text_input("Phone", key="new_contact_phone")
            new_notes = st.text_area("Notes (optional)", key="new_contact_notes", height=80)
            new_primary = st.checkbox("Primary contact for this fund", key="new_contact_primary")

            submitted = st.form_submit_button("Add Contact", type="primary")
            if submitted:
                fund = custom_fund.strip() if new_fund == "(Type new fund name)" else new_fund
                if not fund:
                    st.error("Fund name is required.")
                elif not new_name.strip():
                    st.error("Contact name is required.")
                else:
                    # If marking as primary, unset existing primaries for this fund
                    if new_primary:
                        for existing in db.get_contacts_for_fund(fund):
                            if existing["primary_contact"]:
                                db.update_contact(existing["id"], primary_contact=0)
                    db.add_contact(
                        fund_name=fund,
                        contact_name=new_name.strip(),
                        role=new_role.strip(),
                        email=new_email.strip(),
                        phone=new_phone.strip(),
                        notes=new_notes.strip(),
                        primary_contact=1 if new_primary else 0,
                    )
                    st.success(f"Contact '{esc(new_name.strip())}' added for {esc(fund)}.")


# ═════════════════════════════════════════════
# PAGE: AUDIT LOG
# ═════════════════════════════════════════════
elif page == "Audit Log":
    st.markdown("## Audit Log")
    st.markdown("Complete record of all capital calls processed (persisted in database).")

    all_processed = db.get_processed_calls()
    if not all_processed:
        st.info("No capital calls have been processed yet. Upload a PDF notice to get started.")
    else:
        # ── Filter controls ──
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            date_range = st.date_input(
                "Date Range",
                value=(datetime(2026, 1, 1).date(), datetime.now().date()),
                format="DD.MM.YYYY",
                key="audit_date_range",
            )
        with f2:
            status_filter = st.multiselect(
                "Status", ["EXECUTED", "REJECTED", "ESCALATED"], default=[], key="audit_status"
            )
        with f3:
            fund_filter = st.multiselect(
                "Fund", db.get_unique_funds(), default=[], key="audit_fund"
            )
        with f4:
            reviewer_filter = st.multiselect(
                "Reviewer", db.get_unique_reviewers(), default=[], key="audit_reviewer"
            )

        # Clear filters button
        if st.button("Clear Filters", key="audit_clear_filters"):
            st.session_state["audit_status"] = []
            st.session_state["audit_fund"] = []
            st.session_state["audit_reviewer"] = []
            st.rerun()

        # Build filter args
        date_from = date_range[0] if isinstance(date_range, (list, tuple)) and len(date_range) >= 1 else None
        date_to = date_range[1] if isinstance(date_range, (list, tuple)) and len(date_range) >= 2 else date_from

        filtered = db.get_processed_calls_filtered(
            date_from=date_from,
            date_to=date_to,
            statuses=status_filter or None,
            funds=fund_filter or None,
            reviewer=reviewer_filter or None,
        )

        total_count = len(all_processed)

        # Summary stats
        s1, s2, s3 = st.columns(3)
        executed_count = sum(1 for p in filtered if p["action"] == "EXECUTED")
        rejected_count = sum(1 for p in filtered if p["action"] == "REJECTED")
        escalated_count = sum(1 for p in filtered if p["action"] == "ESCALATED")
        s1.metric("Executed", executed_count)
        s2.metric("Rejected", rejected_count)
        s3.metric("Escalated", escalated_count)

        st.caption(f"Showing {len(filtered)} of {total_count} records")

        audit_export = db.export_audit_log_df()
        st.download_button(
            "📥 Download Audit Log",
            data=to_excel_bytes(audit_export, "Audit Log"),
            file_name=f"audit_log_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.divider()

        # ── Pagination ──
        PAGE_SIZE = 20
        total_pages = max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)
        page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="audit_page")
        page_data = filtered[(page_num - 1) * PAGE_SIZE : page_num * PAGE_SIZE]

        for action in page_data:
            act_type = action.get("action", "")
            if act_type == "EXECUTED":
                badge = '<span class="badge badge-pass">EXECUTED</span>'
            elif act_type == "REJECTED":
                badge = '<span class="badge badge-fail">REJECTED</span>'
            elif act_type == "ESCALATED":
                badge = '<span class="badge badge-pending">ESCALATED</span>'
            else:
                badge = f'<span class="badge badge-fail">{esc(action.get("overall_status", "UNKNOWN"))}</span>'

            fund_display = esc(action.get("fund_name_matched") or action.get("fund_name_extracted") or "Unknown")
            timestamp = esc(action.get("processed_at", ""))
            filename = esc(action.get("filename", "N/A"))
            reviewer_display = esc(action.get("reviewer") or "N/A")

            st.markdown(f"""
            <div class="kpi-card" style="margin-bottom: 1rem;">
                <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;">
                    <div><strong>{fund_display}</strong> &nbsp; {badge}</div>
                    <span style="font-size: 0.8rem; color: #475569;">{timestamp}</span>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.85rem; color: #475569;">
                    Amount: EUR {action.get('amount', 0):,.0f} |
                    File: {filename} |
                    Reviewer: {reviewer_display}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Expandable details
            with st.expander(f"Details: {fund_display}", expanded=False):
                dc1, dc2 = st.columns(2)
                dc1.markdown(f"**Commitment Check:** {'PASS' if action.get('commitment_passed') else 'FAIL'}")
                dc1.caption(action.get("commitment_message", "N/A"))
                dc2.markdown(f"**Wire Check:** {'PASS' if action.get('wire_passed') else 'FAIL'}")
                dc2.caption(action.get("wire_message", "N/A"))
                if action.get("review_notes"):
                    st.markdown(f"**Review Notes:** {esc(action['review_notes'])}")
                if action.get("archive_path") and os.path.exists(action["archive_path"]):
                    with open(action["archive_path"], "rb") as f:
                        st.download_button(
                            "Download Original PDF",
                            data=f.read(),
                            file_name=action.get("filename", "notice.pdf"),
                            mime="application/pdf",
                            key=f"archive_dl_{action.get('id')}",
                        )
                if action.get("email_body") and act_type == "EXECUTED":
                    st.markdown('<div class="section-header">Payment Confirmation Email</div>',
                                unsafe_allow_html=True)
                    st.markdown(f'<div class="email-template">{action["email_body"]}</div>',
                                unsafe_allow_html=True)
                    st.markdown("")
                    call_id = action.get("id")
                    email_already_sent = action.get("email_sent")
                    if email_already_sent:
                        st.markdown(
                            f'<span class="badge badge-pass">Email sent to {esc(action.get("email_recipient", ""))}</span>',
                            unsafe_allow_html=True,
                        )
                    else:
                        audit_recipient = st.text_input(
                            "Recipient Email", placeholder="gp-ops@fundmanager.com",
                            key=f"audit_recipient_{call_id}",
                        )
                        send_disabled = not (audit_recipient and validate_email(audit_recipient) and smtp_configured)
                        al1, al2 = st.columns(2)
                        with al1:
                            if st.button("Send Email", type="primary", use_container_width=True,
                                         disabled=send_disabled, key=f"audit_send_{call_id}"):
                                fund_name = action.get("fund_name_matched") or action.get("fund_name_extracted") or "Unknown"
                                success, message = send_confirmation_email(
                                    smtp_server=st.session_state.get("smtp_server", ""),
                                    smtp_port=st.session_state.get("smtp_port", 587),
                                    smtp_user=st.session_state.get("smtp_user", ""),
                                    smtp_password=st.session_state.get("smtp_pass", ""),
                                    to_email=audit_recipient,
                                    subject=f"Payment Confirmation - Capital Call - {fund_name}",
                                    html_body=action["email_body"],
                                )
                                if success:
                                    db.update_email_status(call_id, audit_recipient)
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        with al2:
                            st.download_button(
                                "Download Email as HTML",
                                data=action["email_body"],
                                file_name=f"confirmation_{call_id}.html",
                                mime="text/html",
                                use_container_width=True,
                                key=f"audit_dl_{call_id}",
                            )
                        if not smtp_configured:
                            st.caption("Configure SMTP settings in the sidebar to enable sending.")
                        if audit_recipient and not validate_email(audit_recipient):
                            st.warning("Please enter a valid email address.")
