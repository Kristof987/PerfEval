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
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)


def average_point_card_html(overall5: float, section_count: int) -> str:
    return f"""<div class="card">
  <div class="card-header">
    <div>
      <div class="card-label">Summarized Evaluation</div>
      <div class="card-title">Average Point</div>
    </div>
    <div class="card-icon" style="background:#eff6ff">⭐</div>
  </div>
  <div class="metric-value">{overall5:.2f}</div>
  <div class="metric-sub">Scale: 1.0 – 5.0 · {section_count} competence</div>
</div>"""


COMPETENCE_MAP_CARD_HTML = """<div class="card" style="min-height:112px;padding-bottom:0.9rem;">
  <div class="card-header" style="margin-bottom:0;">
    <div>
      <div class="card-label">Competence map</div>
      <div class="card-title">Evaluator roles</div>
    </div>
    <div class="card-icon" style="background:#f0f9ff">🎯</div>
  </div>
</div>"""


def evaluation_status_card_html(total_evals: int, unique_roles: int, total_ans: int, unique_forms: int) -> str:
    return f"""<div class="card">
  <div class="card-header">
    <div>
      <div class="card-label">Overview</div>
      <div class="card-title">Evaluation Status</div>
    </div>
    <div class="card-icon" style="background:#f0fdf4">📊</div>
  </div>
  <div class="stat-grid">
    <div class="stat-item"><div class="stat-val">{total_evals}</div><div class="stat-lbl">Evaluations</div></div>
    <div class="stat-item"><div class="stat-val">{unique_roles}</div><div class="stat-lbl">Roles</div></div>
    <div class="stat-item"><div class="stat-val">{total_ans}</div><div class="stat-lbl">Answers</div></div>
    <div class="stat-item"><div class="stat-val">{unique_forms}</div><div class="stat-lbl">Forms</div></div>
  </div>
</div>"""


def progress_row_html(name: str, score: float, color: str, pct: int) -> str:
    return f"""<div class="prog-row">
  <div class="prog-label-row">
    <span>{name}</span>
    <span style="color:{color};font-weight:700">{score:.2f}&nbsp;/&nbsp;5</span>
  </div>
  <div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{pct}%;background:{color}"></div></div>
</div>"""


def competences_card_html(prog_html: str) -> str:
    return f"""<div class="card">
  <div class="card-header">
    <div><div class="card-label">Detailed</div><div class="card-title">Competences</div></div>
    <div class="card-icon" style="background:#faf5ff">🧩</div>
  </div>
  <div style="margin-top:10px">{prog_html}</div>
</div>"""


BY_ROLES_CARD_HTML = """<div class="card" style="min-height:auto;padding-bottom:0.6rem;">
  <div class="card-header" style="margin-bottom:0;">
    <div><div class="card-label">By Roles</div><div class="card-title">Average Point</div></div>
    <div class="card-icon" style="background:#eff6ff">👥</div>
  </div>
</div>"""


CARD_BASE_STYLE = (
    "background:#fff;border:1px solid #e4e8f0;"
    "border-radius:12px;padding:0.85rem 1rem;"
    "margin-bottom:8px;"
    "box-shadow:0 1px 4px rgba(30,50,110,0.04);"
)

LABEL_BASE_STYLE = (
    "font-size:0.67rem;font-family:'JetBrains Mono',monospace;"
    "letter-spacing:0.1em;text-transform:uppercase;color:#94a3b8;"
    "margin-bottom:10px;"
)


def join_str_or_list(val) -> str:
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    return str(val)


def item_rows_html(items: list, accent: str) -> str:
    html = ""
    for item in items:
        html += (
            f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">'
            f'<span style="width:6px;height:6px;border-radius:50%;'
            f'background:{accent};flex-shrink:0;margin-top:6px;"></span>'
            f'<span style="font-size:0.84rem;color:#1a2035;line-height:1.45;">{item}</span>'
            f'</div>'
        )
    return html or '<span style="font-size:0.82rem;color:#94a3b8;">—</span>'


def strength_cards_html(items: list) -> str:
    html = ""
    for s in items:
        comp = join_str_or_list(s.get("competence", ""))
        evid = "".join(
            f'<div style="font-size:0.77rem;color:#64748b;margin-top:4px;'
            f'padding-left:10px;border-left:2px solid #cbd5e1;">{e}</div>'
            for e in s.get("evidence", [])
        )
        html += (
            f'<div style="{CARD_BASE_STYLE}border-left:3px solid #22c55e;">'
            f'<div style="font-size:0.84rem;font-weight:600;color:#0f172a;">{comp}</div>'
            f'{evid}</div>'
        )
    return html


def area_cards_html(items: list) -> str:
    html = ""
    for a in items:
        theme = join_str_or_list(a.get("theme", ""))
        evid = "".join(
            f'<div style="font-size:0.77rem;color:#64748b;margin-top:4px;'
            f'padding-left:10px;border-left:2px solid #cbd5e1;">{e}</div>'
            for e in a.get("evidence", [])
        )
        html += (
            f'<div style="{CARD_BASE_STYLE}border-left:3px solid #f59e0b;">'
            f'<div style="font-size:0.84rem;font-weight:600;color:#0f172a;">{theme}</div>'
            f'{evid}</div>'
        )
    return html
