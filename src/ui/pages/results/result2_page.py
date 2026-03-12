import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from services.result_generation.llm_communication import LLMCommunication

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* Scope font + colours to the main content area only – never touch the sidebar */
section[data-testid="stMain"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: #f0f2f7 !important;
    color: #1a2035;
}
section[data-testid="stMain"] .block-container {
    padding: 1.2rem 1.6rem !important;
    max-width: 100% !important;
}

/* ── Top bar ── */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.3rem;
    padding: 0.85rem 1.3rem;
    background: #fff;
    border-radius: 14px;
    border: 1px solid #e4e8f0;
    box-shadow: 0 1px 6px rgba(30,50,110,0.06);
}
.logo-mark {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, #1d4ed8, #3b82f6);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; color: #fff; font-weight: 800;
    box-shadow: 0 4px 12px rgba(29,78,216,0.25);
}
.app-title  { font-size: 1rem; font-weight: 700; color: #0f172a; letter-spacing: -0.3px; }
.app-sub    { font-size: 0.7rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace; margin-top:1px; }
.period-badge {
    background: #eff6ff; border: 1px solid #bfdbfe;
    color: #1d4ed8; font-size: 0.72rem; font-weight: 600;
    padding: 4px 12px; border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
}
.avatar {
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg, #dbeafe, #bfdbfe);
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700; color: #1d4ed8;
}
.user-name  { font-size: 0.8rem; font-weight: 600; color: #374151; }
.user-role  { font-size: 0.67rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace; }

/* ── Card ── */
.card {
    background: #ffffff;
    border: 1px solid #e4e8f0;
    border-radius: 16px;
    padding: 1.3rem 1.4rem 1rem;
    height: 100%;
    box-shadow: 0 2px 12px rgba(30,50,110,0.05);
}
.card-label {
    font-size: 0.67rem;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 3px;
}
.card-title {
    font-size: 0.92rem; font-weight: 700; color: #0f172a;
    letter-spacing: -0.2px; margin-bottom: 0.2rem;
}
.card-header {
    display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 0.4rem;
}
.card-icon {
    width: 36px; height: 36px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
}

/* Metric */
.metric-value {
    font-size: 2.6rem; font-weight: 800; letter-spacing: -2px;
    color: #0f172a; line-height: 1; margin: 0.5rem 0 0.35rem;
}
.metric-delta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; font-weight: 500;
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 9px; border-radius: 20px;
}
.delta-up   { background: #dcfce7; color: #16a34a; }
.delta-down { background: #fee2e2; color: #dc2626; }
.metric-sub { font-size: 0.7rem; color: #94a3b8; margin-top:7px; font-family:'JetBrains Mono',monospace; }

/* 2x2 stat grid */
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-top: 6px; }
.stat-item {
    background: #f8fafc; border: 1px solid #e9ecf3;
    border-radius: 10px; padding: 10px 12px;
}
.stat-val { font-size: 1.3rem; font-weight: 800; color: #0f172a; letter-spacing: -1px; }
.stat-lbl { font-size: 0.64rem; color: #94a3b8; font-family:'JetBrains Mono',monospace; margin-top:2px; }

/* Progress bars */
.prog-row { margin-bottom: 11px; }
.prog-label-row {
    display: flex; justify-content: space-between;
    font-size: 0.73rem; color: #475569; margin-bottom: 5px; font-weight: 500;
}
.prog-bar-bg { background: #e9ecf3; border-radius: 4px; height: 7px; overflow: hidden; }
.prog-bar-fill { height: 100%; border-radius: 4px; }

/* Activity list */
.activity-item {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 9px 0; border-bottom: 1px solid #f1f5f9;
}
.activity-item:last-child { border-bottom: none; }
.act-icon {
    width: 28px; height: 28px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; flex-shrink: 0; margin-top: 1px;
}
.activity-text { font-size: 0.77rem; color: #374151; flex: 1; font-weight: 500; }
.activity-sub  { font-size: 0.67rem; color: #94a3b8; margin-top: 1px; }
.activity-time { font-size: 0.64rem; color: #cbd5e1; font-family:'JetBrains Mono',monospace; white-space:nowrap; }
</style>
""", unsafe_allow_html=True)

# ── Data ─────────────────────────────────────────────────────────────────────
rng = np.random.default_rng(7)

competencies = ["Kommunikáció", "Csapatmunka", "Szakmai tudás", "Proaktivitás", "Megbízhatóság"]
self_scores  = [4.1, 3.8, 4.5, 3.6, 4.3]
peer_scores  = [3.9, 4.2, 4.4, 3.8, 4.5]
comp_colors  = ["#3b82f6", "#6366f1", "#0ea5e9", "#8b5cf6", "#06b6d4"]

quarters  = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025"]
avg_trend = [3.6, 3.8, 3.9, 4.1, 4.3]

activities_feed = [
    ("#dbeafe", "#1d4ed8", "📋", "Önértékelés beküldve",        "2024 Q4 · Kovács Béla",      "2 napja"),
    ("#dcfce7", "#16a34a", "✅", "Kolléga értékelés lezárva",   "Nagy Anna → Te",              "4 napja"),
    ("#fef3c7", "#d97706", "⏳", "Értékelési határidő közeleg", "2025 Q1 · 5 nap múlva",      "5 napja"),
    ("#f3e8ff", "#7c3aed", "💬", "Vezető visszajelzés érkezett","Tóth Gábor megjegyzése",      "1 hete"),
    ("#fce7f3", "#be185d", "🎯", "Fejlesztési célok frissítve", "3 kompetencia területen",     "2 hete"),
]

PLOT_CFG = dict(displayModeBar=False)
BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#64748b", font_family="Plus Jakarta Sans",
    margin=dict(l=0, r=0, t=4, b=0),
    xaxis=dict(showgrid=False, zeroline=False, showline=False, tickfont_size=9),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.04)", zeroline=False,
               showline=False, tickfont_size=9),
)

def sparkline(y, color="#3b82f6"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(y))), y=y, mode="lines",
        line=dict(color=color, width=2.5),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
    ))
    fig.update_layout(**BASE, height=75)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig

def trend_line():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=quarters, y=avg_trend, mode="lines+markers",
        line=dict(color="#3b82f6", width=2.5),
        marker=dict(color="#fff", size=7, line=dict(color="#3b82f6", width=2.5)),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.07)",
    ))
    fig.update_layout(**BASE, height=110)
    fig.update_xaxes(tickfont_size=9, tickcolor="#cbd5e1")
    fig.update_yaxes(range=[3.0, 5.0], tickfont_size=9)
    return fig

def radar_chart():
    cats = competencies + [competencies[0]]
    s = self_scores + [self_scores[0]]
    p = peer_scores  + [peer_scores[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=s, theta=cats, fill='toself', name='Önértékelés',
        line=dict(color='#3b82f6', width=2),
        fillcolor='rgba(59,130,246,0.10)'))
    fig.add_trace(go.Scatterpolar(
        r=p, theta=cats, fill='toself', name='Kolléga',
        line=dict(color='#6366f1', width=2),
        fillcolor='rgba(99,102,241,0.10)'))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 5], tickfont_size=8,
                            gridcolor="#e9ecf3", linecolor="#e9ecf3"),
            angularaxis=dict(tickfont_size=9, linecolor="#e9ecf3", gridcolor="#e9ecf3"),
        ),
        legend=dict(font_size=9, orientation="h", x=0.5, xanchor="center",
                    y=-0.12, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=30, r=30, t=10, b=30), height=185,
        font_color="#475569",
    )
    return fig

# ── Top bar ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
  <div style="display:flex;align-items:center;gap:12px">
    <div class="logo-mark">ÉR</div>
    <div>
      <div class="app-title">Teljesítményértékelő Rendszer</div>
      <div class="app-sub">performance-review · 2025</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:14px">
    <span class="period-badge">Campaign</span>
    <div style="display:flex;align-items:center;gap:9px">
      <div class="avatar">KÉ</div>
      <div>
        <div class="user-name">Kovács Éva</div>
        <div class="user-role">senior analyst</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Row 1 ────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([1.05, 1.1, 0.85], gap="medium")

with c1:
    st.markdown("""
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-label">Önértékelés · 2025 Q1</div>
          <div class="card-title">Összesített Pontszám</div>
        </div>
        <div class="card-icon" style="background:#eff6ff">⭐</div>
      </div>
      <div class="metric-value">4.24</div>
      <span class="metric-delta delta-up">▲ +0.14 előző negyedévhez</span>
      <div class="metric-sub">Skála: 1.0 – 5.0 · 5 kompetencia</div>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(sparkline(avg_trend), use_container_width=True,
                    config=PLOT_CFG, key="sp1")

with c2:
    st.markdown("""
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-label">Kompetencia térkép</div>
          <div class="card-title">Én vs. Kollégák</div>
        </div>
        <div class="card-icon" style="background:#f0f9ff">🎯</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(radar_chart(), use_container_width=True,
                    config=PLOT_CFG, key="radar")

with c3:
    st.markdown("""
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-label">Áttekintő</div>
          <div class="card-title">Értékelési Státusz</div>
        </div>
        <div class="card-icon" style="background:#f0fdf4">📊</div>
      </div>
      <div class="stat-grid">
        <div class="stat-item">
          <div class="stat-val">3/5</div>
          <div class="stat-lbl">Beküldve</div>
        </div>
        <div class="stat-item">
          <div class="stat-val">4.38</div>
          <div class="stat-lbl">Kolléga átlag</div>
        </div>
        <div class="stat-item">
          <div class="stat-val">12</div>
          <div class="stat-lbl">Visszajelzések</div>
        </div>
        <div class="stat-item">
          <div class="stat-val">87%</div>
          <div class="stat-lbl">Kitöltöttség</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── Row 2 ────────────────────────────────────────────────────────────────────
c4, c5, c6 = st.columns([1, 1, 1], gap="medium")

with c4:
    st.markdown("""
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-label">5 negyedév</div>
          <div class="card-title">Fejlődési Trend</div>
        </div>
        <div class="card-icon" style="background:#eff6ff">📈</div>
      </div>
      <span class="metric-delta delta-up" style="font-size:0.68rem">▲ +0.7 az elmúlt évben</span>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(trend_line(), use_container_width=True,
                    config=PLOT_CFG, key="trend")

with c5:
    prog_html = ""
    for comp, sc, col in zip(competencies, self_scores, comp_colors):
        pct = int(sc / 5 * 100)
        prog_html += f"""
        <div class="prog-row">
          <div class="prog-label-row">
            <span>{comp}</span>
            <span style="color:{col};font-weight:700">{sc:.1f} / 5</span>
          </div>
          <div class="prog-bar-bg">
            <div class="prog-bar-fill" style="width:{pct}%;background:{col}"></div>
          </div>
        </div>"""
    st.markdown(f"""
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-label">Részletes</div>
          <div class="card-title">Kompetenciák</div>
        </div>
        <div class="card-icon" style="background:#faf5ff">🧩</div>
      </div>
      <div style="margin-top:10px">{prog_html}</div>
    </div>
    """, unsafe_allow_html=True)

#with c6:
    #llm_comm = LLMCommunication()
    #response = llm_comm.request("He expresses himself fine. He always explains us his tasks and the solutions he created for it. He has really good performance skills! -> From this text, collects strength and weakness")
    #st.write(response)