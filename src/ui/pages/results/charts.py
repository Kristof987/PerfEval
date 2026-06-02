import streamlit as st
import plotly.graph_objects as go

from ui.pages.results.consts import BASE_LAY, COMP_COLS, FILL_RGBA, PLOT_CFG, ROLE_COLS
from ui.pages.results.results_styles import (
    inject_dashboard_css,
    average_point_card_html,
    COMPETENCE_MAP_CARD_HTML,
    evaluation_status_card_html,
    progress_row_html,
    competences_card_html,
    BY_ROLES_CARD_HTML,
)


def sparkline_fig(y: list) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(y))), y=y, mode="lines",
        line=dict(color="#3b82f6", width=2.5),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
    ))
    fig.update_layout(
        **{**BASE_LAY, "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)"},
        height=75,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def radar_fig(section_names: list, role_avgs: dict) -> go.Figure | None:
    if not section_names:
        return None
    snames = section_names[:]
    pad_idx = 0
    while len(snames) < 3:
        pad_idx += 1
        snames.append("\u200b" * pad_idx)
    cats = snames + [snames[0]]
    fig = go.Figure()
    for i, (role, avgs) in enumerate(role_avgs.items()):
        padded = (avgs + [0.0, 0.0])[:len(snames)]
        fig.add_trace(go.Scatterpolar(
            r=padded + [padded[0]], theta=cats,
            fill="toself", name=role,
            line=dict(color=ROLE_COLS[i % len(ROLE_COLS)], width=2),
            fillcolor=FILL_RGBA[i % len(FILL_RGBA)],
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="#ffffff",
            radialaxis=dict(visible=True, range=[0, 5], tickfont_size=8, gridcolor="#e9ecf3", linecolor="#e9ecf3"),
            angularaxis=dict(tickfont_size=9, linecolor="#e9ecf3", gridcolor="#e9ecf3"),
        ),
        legend=dict(font_size=9, orientation="h", x=0.5, xanchor="center", y=-0.08, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=30, r=30, t=10, b=22), height=230,
        font_color="#475569",
    )
    return fig


def render_summary_dashboard(evaluations: list, key_prefix: str = "overall"):
    if not evaluations:
        st.info("No completed evaluations found for this campaign.")
        return
    if len(evaluations) < 3:
        st.warning("Low data quality: fewer than 3 completed evaluations. Insights may be unstable.")
    inject_dashboard_css()
    _sec_ratings: dict = {}
    _role_sec_rtg: dict = {}
    for ev in evaluations:
        _role = ev["evaluator_role"]
        for _sec in ev["sections"]:
            _st = _sec.get("title", "General")
            for _q in _sec.get("questions", []):
                if not isinstance(_q, dict) or _q.get("type") != "rating":
                    continue
                _qid = str(_q.get("id", ""))
                _rmax = float(_q.get("rating_max", 5))
                _ans = ev["answers"].get(_qid)
                if _ans is None or _ans == "":
                    continue
                if isinstance(_ans, dict):
                    _ans = _ans.get("rating")
                if _ans is not None:
                    try:
                        _v = float(_ans)
                        _sec_ratings.setdefault(_st, []).append((_v, _rmax))
                        _role_sec_rtg.setdefault(_role, {}).setdefault(_st, []).append((_v, _rmax))
                    except (ValueError, TypeError):
                        pass
    section_names: list = []
    section_avgs_5: list = []
    for _sn, _rts in _sec_ratings.items():
        if _rts:
            _a5 = sum(_v / _m * 5 for _v, _m in _rts) / len(_rts)
            section_names.append(_sn)
            section_avgs_5.append(round(_a5, 2))
    _all_vals = [_v / _m * 5 for _rts in _sec_ratings.values() for _v, _m in _rts]
    _overall5 = round(sum(_all_vals) / len(_all_vals), 2) if _all_vals else 0.0
    _role_avgs: dict = {}
    for _role, _sdct in _role_sec_rtg.items():
        _role_avgs[_role] = [
            round(sum(_v / _m * 5 for _v, _m in _sdct[_sn]) / len(_sdct[_sn]), 2)
            if _sdct.get(_sn) else 0.0
            for _sn in section_names
        ]
    _total_evals = len(evaluations)
    _unique_roles = len(set(ev["evaluator_role"] for ev in evaluations))
    _unique_forms = len(set(ev["form_name"] for ev in evaluations))
    _total_ans = sum(len(v) for v in _sec_ratings.values())
    _cr1, _cr2, _cr3 = st.columns([1.05, 1.1, 0.85], gap="medium")
    with _cr1:
        st.markdown(average_point_card_html(_overall5, len(section_names)), unsafe_allow_html=True)
        if section_avgs_5:
            st.plotly_chart(sparkline_fig(section_avgs_5), use_container_width=True, config=PLOT_CFG, key=f"{key_prefix}_sparkline")
    with _cr2:
        st.markdown(COMPETENCE_MAP_CARD_HTML, unsafe_allow_html=True)
        _rfig = radar_fig(section_names, _role_avgs)
        if _rfig:
            st.plotly_chart(_rfig, use_container_width=True, config=PLOT_CFG, key=f"{key_prefix}_radar")
        else:
            st.caption("Nincs értékelési adat a radarhoz.")
    with _cr3:
        st.markdown(evaluation_status_card_html(_total_evals, _unique_roles, _total_ans, _unique_forms), unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    _cr4, _cr5 = st.columns([1, 1], gap="medium")
    with _cr4:
        if section_names:
            _prog = ""
            for _cn, _sc, _cl in zip(section_names, section_avgs_5, (COMP_COLS * (len(section_names) // len(COMP_COLS) + 1))):
                _pct = int(_sc / 5 * 100)
                _prog += progress_row_html(_cn, _sc, _cl, _pct)
            st.markdown(competences_card_html(_prog), unsafe_allow_html=True)
        else:
            st.info("No rating questions found in the evaluations.")
    with _cr5:
        if _role_avgs:
            _rnames = list(_role_avgs.keys())
            _rovrl = [
                round(sum(_a for _a in _avgs if _a > 0) / max(sum(1 for _a in _avgs if _a > 0), 1), 2)
                for _avgs in _role_avgs.values()
            ]
            _rb_fig = go.Figure(data=[go.Bar(
                x=_rnames, y=_rovrl,
                marker_color=(ROLE_COLS * (len(_rnames) // len(ROLE_COLS) + 1))[:len(_rnames)],
                text=[f"{_v:.2f}" for _v in _rovrl],
                textposition="auto",
            )])
            _rb_fig.update_layout(
                **{**BASE_LAY, "margin": dict(l=10, r=10, t=4, b=30), "paper_bgcolor": "#ffffff", "plot_bgcolor": "#ffffff"},
                yaxis=dict(range=[0, 5], title="Score (1-5)", showgrid=True, gridcolor="rgba(0,0,0,0.04)", zeroline=False, showline=False, tickfont_size=9),
                xaxis=dict(showgrid=False, zeroline=False, showline=False, tickfont_size=9),
                height=160,
            )
            st.markdown(BY_ROLES_CARD_HTML, unsafe_allow_html=True)
            st.plotly_chart(_rb_fig, use_container_width=True, config=PLOT_CFG, key=f"{key_prefix}_role_bar")
        else:
            st.info("No evaluator role data available.")
