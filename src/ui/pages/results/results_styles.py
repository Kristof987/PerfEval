"""Shared HTML/CSS styles for the results pages."""
import streamlit as st

DASHBOARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
section[data-testid="stMain"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: #f0f2f7 !important;
    color: #1a2035;
}
section[data-testid="stMain"] .block-container { padding: 1.2rem 1.6rem !important; max-width: 100% !important; }
.card {
    background:#fff;
    border:1px solid #e4e8f0;
    border-radius:16px;
    padding:1.3rem 1.4rem 1rem;
    height:100%;
    min-height:240px;
    box-shadow:0 2px 12px rgba(30,50,110,0.05);
    display:flex;
    flex-direction:column;
}
.card-label { font-size:0.67rem; font-family:'JetBrains Mono',monospace; letter-spacing:0.1em; text-transform:uppercase; color:#94a3b8; margin-bottom:3px; }
.card-title { font-size:0.92rem; font-weight:700; color:#0f172a; letter-spacing:-0.2px; margin-bottom:0.2rem; }
.card-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.4rem; }
.card-icon { width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:16px; flex-shrink:0; }
.metric-value { font-size:2.6rem; font-weight:800; letter-spacing:-2px; color:#0f172a; line-height:1; margin:0.5rem 0 0.35rem; }
.metric-sub { font-size:0.7rem; color:#94a3b8; margin-top:7px; font-family:'JetBrains Mono',monospace; }
.stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:9px; margin-top:6px; }
.card .stat-grid { margin-top:auto; }
.stat-item { background:#f8fafc; border:1px solid #e9ecf3; border-radius:10px; padding:10px 12px; }
.stat-val { font-size:1.3rem; font-weight:800; color:#0f172a; letter-spacing:-1px; }
.stat-lbl { font-size:0.64rem; color:#94a3b8; font-family:'JetBrains Mono',monospace; margin-top:2px; }
.prog-row { margin-bottom:11px; }
.prog-label-row { display:flex; justify-content:space-between; font-size:0.73rem; color:#475569; margin-bottom:5px; font-weight:500; }
.prog-bar-bg { background:#e9ecf3; border-radius:4px; height:7px; overflow:hidden; }
.prog-bar-fill { height:100%; border-radius:4px; }
</style>
"""


def inject_dashboard_css() -> None:
    """Inject the shared dashboard CSS into the Streamlit page."""
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
