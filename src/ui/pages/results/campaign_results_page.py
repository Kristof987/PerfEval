import io
import os
import sys
import json
import subprocess
import openpyxl
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from persistence.db.connection import get_db
from persistence.repository.campaign_repo import CampaignRepository

# Initialize repositories
campaign_repo = CampaignRepository()
db = get_db()

# -------------------------
# Session State Init
# -------------------------
if "cr_view" not in st.session_state:
    st.session_state.cr_view = "campaign"  # "campaign" or "employee"
if "cr_selected_campaign_id" not in st.session_state:
    st.session_state.cr_selected_campaign_id = None
if "cr_selected_campaign_name" not in st.session_state:
    st.session_state.cr_selected_campaign_name = None
if "cr_selected_employee_id" not in st.session_state:
    st.session_state.cr_selected_employee_id = None
if "cr_selected_employee_name" not in st.session_state:
    st.session_state.cr_selected_employee_name = None


# -----------------------------------------------------------------------
# Helper: normalize f.questions → {"sections": [...]}
# -----------------------------------------------------------------------
def _normalize_questions(raw) -> dict:
    """
    f.questions can arrive as:
      - Python dict  (psycopg2 decoded jsonb)
      - Python list  (legacy flat question list)
      - JSON string  (text / json column)
      - None
    Always returns {"sections": [{"id": ..., "title": ..., "questions": [...]}]}
    """
    if raw is None:
        return {"sections": []}
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {"sections": []}
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return {"sections": []}
    # legacy: flat list of question dicts
    if isinstance(raw, list):
        return {"sections": [{"id": "legacy", "title": "General", "questions": raw}]}
    # current: {"sections": [...]}
    if isinstance(raw, dict) and "sections" in raw:
        return raw
    return {"sections": []}


# -----------------------------------------------------------------------
# Helper: collect all completed evaluations for a campaign as a JSON-
# serialisable dict, ready to be passed to result_generation/main.py
# -----------------------------------------------------------------------
def get_campaign_qa_json(conn, campaign_id: int, campaign_name: str) -> dict:
    """
    Returns a dict structured as::

        {
            "campaign_id":   int,
            "campaign_name": str,
            "forms": {
                "<form_name>": [
                    {
                        "question":      str,
                        "question_type": str,
                        "competence":    str,
                        "options":       list,   # only for multiple_choice / slider_labels
                        "answers": [
                            {
                                "evaluatee_name": str,
                                "evaluator_role": str,
                                "answer":         any
                            },
                            ...
                        ]
                    },
                    ...
                ],
                ...
            }
        }
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT
            eval_tee.name          AS evaluatee_name,
            eval_tor.org_role_name AS evaluator_role,
            f.name                 AS form_name,
            e.answers,
            f.questions
        FROM evaluation e
        JOIN organisation_employees eval_tee ON e.evaluatee_id = eval_tee.id
        JOIN organisation_employees eval_tor ON e.evaluator_id = eval_tor.id
        JOIN form f ON e.form_id = f.id
        WHERE e.campaign_id = %s
          AND e.status = 'completed'
        ORDER BY f.name, eval_tee.name
    """, (campaign_id,))

    # form_name -> OrderedDict of q_id -> question entry (with "answers" list)
    form_questions: dict = {}

    for row in cur.fetchall():
        evaluatee_name = row[0]
        evaluator_role = row[1] or "Unknown"
        form_name      = row[2]
        answers        = row[3]
        questions_raw  = row[4]

        # --- parse answers ---
        if isinstance(answers, str):
            try:
                answers = json.loads(answers)
            except (json.JSONDecodeError, ValueError):
                answers = {}
        elif answers is None:
            answers = {}

        # --- parse questions into sections ---
        content  = _normalize_questions(questions_raw)
        sections = content.get("sections", [])

        # Build the question skeleton for this form on first encounter
        if form_name not in form_questions:
            form_questions[form_name] = {}
            for section in sections:
                section_title = section.get("title", "General")
                for q in section.get("questions", []):
                    if not isinstance(q, dict):
                        continue
                    q_id   = str(q.get("id", ""))
                    q_type = q.get("type", "text")

                    entry: dict = {
                        "question":      q.get("text", ""),
                        "question_type": q_type,
                        "competence":    section_title,
                        "answers":       [],
                    }
                    # Attach selectable options where relevant
                    if q_type == "multiple_choice":
                        entry["options"] = q.get("options", [])
                    elif q_type == "slider_labels":
                        entry["options"] = q.get("slider_options", [])

                    form_questions[form_name][q_id] = entry

        # --- attach each evaluator's answer to the matching question ---
        for q_id, q_entry in form_questions[form_name].items():
            answer_raw = answers.get(q_id)

            # Flatten legacy dict-wrapper answers
            if isinstance(answer_raw, dict):
                if "rating" in answer_raw:
                    answer_raw = answer_raw["rating"]
                elif "choice" in answer_raw:
                    answer_raw = answer_raw["choice"]
                elif "text" in answer_raw:
                    answer_raw = answer_raw["text"]

            if answer_raw is not None and answer_raw != "":
                q_entry["answers"].append({
                    "evaluatee_name": evaluatee_name,
                    "evaluator_role": evaluator_role,
                    "answer":         answer_raw,
                })

    cur.close()

    return {
        "campaign_id":   campaign_id,
        "campaign_name": campaign_name,
        "forms": {
            form_name: list(questions_by_id.values())
            for form_name, questions_by_id in form_questions.items()
        },
    }


# -----------------------------------------------------------------------
# Helper: render a single answer value given the question definition
# -----------------------------------------------------------------------
def _render_answer(answer, question: dict):
    q_type = question.get("type", "text")
    if answer is None or answer == "":
        st.caption("_(no answer)_")
        return
    # answers may be stored as a legacy dict wrapper {rating:…, choice:…, text:…}
    if isinstance(answer, dict):
        if "rating" in answer:
            hi = question.get("rating_max", 5)
            st.write(f"⭐ {answer['rating']}/{hi}")
        if "choice" in answer:
            st.write(f"☑️ {answer['choice']}")
        if "text" in answer:
            st.write(f"📝 {answer['text']}")
        return
    # scalar values (current storage format)
    if q_type == "rating":
        hi = question.get("rating_max", 5)
        st.write(f"⭐ {answer}/{hi}")
    elif q_type == "multiple_choice":
        st.write(f"☑️ {answer}")
    elif q_type == "slider_labels":
        st.write(f"🎚️ {answer}")
    else:
        st.write(f"📝 {answer}")


# =========================================================
# EMPLOYEE RESULT VIEW
# =========================================================
if st.session_state.cr_view == "employee":

    if st.button("← Back to Campaign Results"):
        st.session_state.cr_view = "campaign"
        st.session_state.cr_selected_employee_id = None
        st.session_state.cr_selected_employee_name = None
        st.rerun()

    st.title("Employee Evaluation Results")
    st.markdown(f"### {st.session_state.cr_selected_employee_name}")
    st.caption(f"Campaign: {st.session_state.cr_selected_campaign_name}")
    st.divider()

    employee_id = st.session_state.cr_selected_employee_id
    campaign_id = st.session_state.cr_selected_campaign_id

    # Fetch all completed evaluations for this employee in this campaign
    with db.connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                e.id,
                eval_tor.name          AS evaluator_name,
                eval_tor.org_role_name AS evaluator_role,
                f.id                   AS form_id,
                f.name                 AS form_name,
                e.answers,
                e.finish_date,
                f.questions
            FROM evaluation e
            JOIN organisation_employees eval_tor ON e.evaluator_id = eval_tor.id
            JOIN form f ON e.form_id = f.id
            WHERE e.evaluatee_id = %s
              AND e.campaign_id  = %s
              AND e.status       = 'completed'
            ORDER BY f.name, eval_tor.org_role_name, eval_tor.name
        """, (employee_id, campaign_id))

        evaluations = []
        for r in cur.fetchall():
            answers = r[5]
            if isinstance(answers, str):
                try:
                    answers = json.loads(answers)
                except (json.JSONDecodeError, ValueError):
                    answers = {}
            elif answers is None:
                answers = {}

            content = _normalize_questions(r[7])

            evaluations.append({
                "id":             r[0],
                "evaluator_name": r[1],
                "evaluator_role": r[2] or "Unknown",
                "form_id":        r[3],
                "form_name":      r[4],
                "answers":        answers,
                "finish_date":    r[6],
                "sections":       content["sections"],
            })
        cur.close()

    tab_answers, tab_results = st.tabs(["📝 Answers", "📊 Results"])

    with tab_answers:
        if not evaluations:
            st.info("No completed evaluations found for this employee in this campaign.")
        else:
            # Build distinct form list (preserving appearance order)
            seen_form_ids: set = set()
            form_options: list = []
            for ev in evaluations:
                if ev["form_id"] not in seen_form_ids:
                    seen_form_ids.add(ev["form_id"])
                    form_options.append(ev["form_name"])

            # Form filter – only rendered when there are multiple forms
            if len(form_options) > 1:
                selected_forms = st.multiselect(
                    "Filter by form",
                    options=form_options,
                    default=form_options,
                    placeholder="Select forms to display…",
                )
            else:
                selected_forms = form_options

            filtered_evals = [ev for ev in evaluations if ev["form_name"] in selected_forms]

            if not filtered_evals:
                st.info("No evaluations match the selected forms.")
            else:
                # ── Group: form → evaluator_role → [evaluations] ─────────────
                evals_by_form: dict = {}
                for ev in filtered_evals:
                    evals_by_form.setdefault(ev["form_name"], {}).setdefault(
                        ev["evaluator_role"], []
                    ).append(ev)

                for form_name, roles_dict in evals_by_form.items():
                    st.subheader(f"📋 {form_name}")

                    # Use the first evaluation's sections as the question template
                    first_eval = next(iter(next(iter(roles_dict.values()))))
                    sections   = first_eval["sections"]

                    if not sections:
                        st.caption("_(no questions in this form)_")
                    else:
                        for role_name, role_evals in roles_dict.items():
                            st.markdown(f"#### 👤 {role_name}")

                            for section in sections:
                                sec_title = section.get("title", "")
                                questions = section.get("questions", [])
                                if sec_title:
                                    st.markdown(f"**{sec_title}**")

                                for q in questions:
                                    if not isinstance(q, dict):
                                        continue
                                    q_id   = str(q.get("id", ""))
                                    q_text = q.get("text", "Question")

                                    with st.container(border=True):
                                        st.markdown(f"**{q_text}**")
                                        any_answer = False
                                        for ev in role_evals:
                                            answer = ev["answers"].get(q_id)
                                            if answer is not None and answer != "":
                                                _render_answer(answer, q)
                                                any_answer = True
                                        if not any_answer:
                                            st.caption("_(no answers)_")

                    st.divider()

    with tab_results:
        if not evaluations:
            st.info("No completed evaluations found for this employee in this campaign.")
        else:
            # ── CSS (result2_page style) ──────────────────────────────────────
            st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
section[data-testid="stMain"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: #f0f2f7 !important;
    color: #1a2035;
}
section[data-testid="stMain"] .block-container { padding: 1.2rem 1.6rem !important; max-width: 100% !important; }
.card { background:#fff; border:1px solid #e4e8f0; border-radius:16px; padding:1.3rem 1.4rem 1rem; height:100%; box-shadow:0 2px 12px rgba(30,50,110,0.05); }
.card-label { font-size:0.67rem; font-family:'JetBrains Mono',monospace; letter-spacing:0.1em; text-transform:uppercase; color:#94a3b8; margin-bottom:3px; }
.card-title { font-size:0.92rem; font-weight:700; color:#0f172a; letter-spacing:-0.2px; margin-bottom:0.2rem; }
.card-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.4rem; }
.card-icon { width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:16px; flex-shrink:0; }
.metric-value { font-size:2.6rem; font-weight:800; letter-spacing:-2px; color:#0f172a; line-height:1; margin:0.5rem 0 0.35rem; }
.metric-sub { font-size:0.7rem; color:#94a3b8; margin-top:7px; font-family:'JetBrains Mono',monospace; }
.stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:9px; margin-top:6px; }
.stat-item { background:#f8fafc; border:1px solid #e9ecf3; border-radius:10px; padding:10px 12px; }
.stat-val { font-size:1.3rem; font-weight:800; color:#0f172a; letter-spacing:-1px; }
.stat-lbl { font-size:0.64rem; color:#94a3b8; font-family:'JetBrains Mono',monospace; margin-top:2px; }
.prog-row { margin-bottom:11px; }
.prog-label-row { display:flex; justify-content:space-between; font-size:0.73rem; color:#475569; margin-bottom:5px; font-weight:500; }
.prog-bar-bg { background:#e9ecf3; border-radius:4px; height:7px; overflow:hidden; }
.prog-bar-fill { height:100%; border-radius:4px; }
</style>""", unsafe_allow_html=True)

            # ── Compute statistics ────────────────────────────────────────────
            _sec_ratings: dict = {}       # sec -> [(val, max)]
            _role_sec_rtg: dict = {}      # role -> {sec -> [(val, max)]}

            for ev in evaluations:
                _role = ev["evaluator_role"]
                for _sec in ev["sections"]:
                    _st = _sec.get("title", "General")
                    for _q in _sec.get("questions", []):
                        if not isinstance(_q, dict) or _q.get("type") != "rating":
                            continue
                        _qid  = str(_q.get("id", ""))
                        _rmax = float(_q.get("rating_max", 5))
                        _ans  = ev["answers"].get(_qid)
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

            # Section names + per-section averages on 0–5 scale
            section_names:  list = []
            section_avgs_5: list = []
            for _sn, _rts in _sec_ratings.items():
                if _rts:
                    _a5 = sum(_v / _m * 5 for _v, _m in _rts) / len(_rts)
                    section_names.append(_sn)
                    section_avgs_5.append(round(_a5, 2))

            # Overall average (0–5)
            _all_vals  = [_v / _m * 5 for _rts in _sec_ratings.values() for _v, _m in _rts]
            _overall5  = round(sum(_all_vals) / len(_all_vals), 2) if _all_vals else 0.0

            # Per-role per-section averages for radar
            _role_avgs: dict = {}
            for _role, _sdct in _role_sec_rtg.items():
                _role_avgs[_role] = [
                    round(sum(_v / _m * 5 for _v, _m in _sdct[_sn]) / len(_sdct[_sn]), 2)
                    if _sdct.get(_sn) else 0.0
                    for _sn in section_names
                ]

            # Summary counts
            _total_evals  = len(evaluations)
            _unique_roles = len(set(ev["evaluator_role"] for ev in evaluations))
            _unique_forms = len(set(ev["form_name"] for ev in evaluations))
            _total_ans    = sum(len(v) for v in _sec_ratings.values())

            # Colour palettes
            _ROLE_COLS = ["#3b82f6", "#6366f1", "#0ea5e9", "#8b5cf6", "#06b6d4", "#f59e0b"]
            _COMP_COLS = ["#3b82f6", "#6366f1", "#0ea5e9", "#8b5cf6", "#06b6d4",
                          "#f59e0b", "#10b981", "#f43f5e"]
            _FILL_RGBA = ["rgba(59,130,246,0.10)", "rgba(99,102,241,0.10)",
                          "rgba(14,165,233,0.10)", "rgba(139,92,246,0.10)",
                          "rgba(6,182,212,0.10)",  "rgba(245,158,11,0.10)"]
            _PLOT_CFG  = dict(displayModeBar=False)
            _BASE_LAY  = dict(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#64748b", font_family="Plus Jakarta Sans",
                margin=dict(l=0, r=0, t=4, b=0),
            )

            # Sparkline helper
            def _sparkline_fig(_y):
                _fig = go.Figure()
                _fig.add_trace(go.Scatter(
                    x=list(range(len(_y))), y=_y, mode="lines",
                    line=dict(color="#3b82f6", width=2.5),
                    fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
                ))
                _fig.update_layout(**_BASE_LAY, height=75)
                _fig.update_xaxes(visible=False)
                _fig.update_yaxes(visible=False)
                return _fig

            # Radar helper
            def _radar_fig():
                if not section_names:
                    return None
                # Scatterpolar needs ≥ 3 unique angular positions to render a
                # visible polygon.  Pad with invisible placeholder spokes when
                # the real data has fewer sections.
                _snames = section_names[:]
                _pad_idx = 0
                while len(_snames) < 3:
                    _pad_idx += 1
                    _snames.append("\u200b" * _pad_idx)   # zero-width-space chars → unique but invisible labels
                _cats = _snames + [_snames[0]]
                _fig  = go.Figure()
                for _i, (_r, _avgs) in enumerate(_role_avgs.items()):
                    # Extend avgs with 0.0 for any padded spokes
                    _padded = (_avgs + [0.0, 0.0])[:len(_snames)]
                    _fig.add_trace(go.Scatterpolar(
                        r=_padded + [_padded[0]], theta=_cats,
                        fill="toself", name=_r,
                        line=dict(color=_ROLE_COLS[_i % len(_ROLE_COLS)], width=2),
                        fillcolor=_FILL_RGBA[_i % len(_FILL_RGBA)],
                    ))
                _fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    polar=dict(
                        bgcolor="rgba(0,0,0,0)",
                        radialaxis=dict(visible=True, range=[0, 5], tickfont_size=8,
                                        gridcolor="#e9ecf3", linecolor="#e9ecf3"),
                        angularaxis=dict(tickfont_size=9, linecolor="#e9ecf3", gridcolor="#e9ecf3"),
                    ),
                    legend=dict(font_size=9, orientation="h", x=0.5, xanchor="center",
                                y=-0.12, bgcolor="rgba(0,0,0,0)"),
                    margin=dict(l=30, r=30, t=10, b=30), height=230,
                    font_color="#475569",
                )
                return _fig

            # ── Row 1: score card | radar | stat grid ─────────────────────────
            _cr1, _cr2, _cr3 = st.columns([1.05, 1.1, 0.85], gap="medium")

            with _cr1:
                st.markdown(f"""
<div class="card">
  <div class="card-header">
    <div>
      <div class="card-label">Summarized Evaluation</div>
      <div class="card-title">Average Point</div>
    </div>
    <div class="card-icon" style="background:#eff6ff">⭐</div>
  </div>
  <div class="metric-value">{_overall5:.2f}</div>
  <div class="metric-sub">Scale: 1.0 – 5.0 · {len(section_names)} competence</div>
</div>""", unsafe_allow_html=True)
                if section_avgs_5:
                    st.plotly_chart(_sparkline_fig(section_avgs_5),
                                    use_container_width=True, config=_PLOT_CFG,
                                    key="emp_sparkline")

            with _cr2:
                st.markdown("""
<div class="card">
  <div class="card-header">
    <div>
      <div class="card-label">Competence map</div>
      <div class="card-title">Evaluator roles</div>
    </div>
    <div class="card-icon" style="background:#f0f9ff">🎯</div>
  </div>
</div>""", unsafe_allow_html=True)
                _rfig = _radar_fig()
                if _rfig:
                    st.plotly_chart(_rfig, use_container_width=True,
                                    config=_PLOT_CFG, key="emp_radar")
                else:
                    st.caption("Nincs értékelési adat a radarhoz.")

            with _cr3:
                st.markdown(f"""
<div class="card">
  <div class="card-header">
    <div>
      <div class="card-label">Overview</div>
      <div class="card-title">Evaluation Status</div>
    </div>
    <div class="card-icon" style="background:#f0fdf4">📊</div>
  </div>
  <div class="stat-grid">
    <div class="stat-item"><div class="stat-val">{_total_evals}</div><div class="stat-lbl">Evaluations</div></div>
    <div class="stat-item"><div class="stat-val">{_unique_roles}</div><div class="stat-lbl">Roles</div></div>
    <div class="stat-item"><div class="stat-val">{_total_ans}</div><div class="stat-lbl">Answers</div></div>
    <div class="stat-item"><div class="stat-val">{_unique_forms}</div><div class="stat-lbl">Forms</div></div>
  </div>
</div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            # ── Row 2: competence bars | role averages bar chart ───────────────
            _cr4, _cr5 = st.columns([1, 1], gap="medium")

            with _cr4:
                if section_names:
                    _prog = ""
                    for _cn, _sc, _cl in zip(
                        section_names, section_avgs_5,
                        (_COMP_COLS * (len(section_names) // len(_COMP_COLS) + 1)),
                    ):
                        _pct = int(_sc / 5 * 100)
                        _prog += f"""
<div class="prog-row">
  <div class="prog-label-row">
    <span>{_cn}</span>
    <span style="color:{_cl};font-weight:700">{_sc:.2f}&nbsp;/&nbsp;5</span>
  </div>
  <div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{_pct}%;background:{_cl}"></div></div>
</div>"""
                    st.markdown(f"""
<div class="card">
  <div class="card-header">
    <div><div class="card-label">Detailed</div><div class="card-title">Competences</div></div>
    <div class="card-icon" style="background:#faf5ff">🧩</div>
  </div>
  <div style="margin-top:10px">{_prog}</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.info("No rating questions found in the evaluations.")

            with _cr5:
                if _role_avgs:
                    _rnames = list(_role_avgs.keys())
                    _rovrl  = [
                        round(sum(_a for _a in _avgs if _a > 0) / max(sum(1 for _a in _avgs if _a > 0), 1), 2)
                        for _avgs in _role_avgs.values()
                    ]
                    _rb_fig = go.Figure(data=[go.Bar(
                        x=_rnames, y=_rovrl,
                        marker_color=(_ROLE_COLS * (len(_rnames) // len(_ROLE_COLS) + 1))[:len(_rnames)],
                        text=[f"{_v:.2f}" for _v in _rovrl],
                        textposition="auto",
                    )])
                    _rb_fig.update_layout(
                        **{**_BASE_LAY, "margin": dict(l=10, r=10, t=4, b=30)},
                        yaxis=dict(range=[0, 5], showgrid=True, gridcolor="rgba(0,0,0,0.04)",
                                   zeroline=False, showline=False, tickfont_size=9),
                        xaxis=dict(showgrid=False, zeroline=False, showline=False, tickfont_size=9),
                        height=160,
                    )
                    st.markdown("""
<div class="card">
  <div class="card-header">
    <div><div class="card-label">By Roles</div><div class="card-title">Average Point</div></div>
    <div class="card-icon" style="background:#eff6ff">👥</div>
  </div>
</div>""", unsafe_allow_html=True)
                    st.plotly_chart(_rb_fig, use_container_width=True,
                                    config=_PLOT_CFG, key="emp_role_bar")
                else:
                    st.info("No evaluator role data available.")

            # ── AI Analysis ──────────────────────────────────────────────────
            st.divider()
            st.subheader("🤖 AI Analysis")

            if st.button(
                "Generate AI Results",
                key="btn_generate_ai_results_emp",
                type="primary",
                help="Run the AI pipeline for this employee's completed evaluations.",
            ):
                # Build employee-scoped payload (same structure as get_campaign_qa_json)
                emp_name = st.session_state.cr_selected_employee_name
                form_questions_emp: dict = {}
                for ev in evaluations:
                    fn      = ev["form_name"]
                    ev_role = ev["evaluator_role"]
                    if fn not in form_questions_emp:
                        form_questions_emp[fn] = {}
                        for section in ev["sections"]:
                            sec_title = section.get("title", "General")
                            for q in section.get("questions", []):
                                if not isinstance(q, dict):
                                    continue
                                q_id   = str(q.get("id", ""))
                                q_type = q.get("type", "text")
                                entry: dict = {
                                    "question":      q.get("text", ""),
                                    "question_type": q_type,
                                    "competence":    sec_title,
                                    "answers":       [],
                                }
                                if q_type == "multiple_choice":
                                    entry["options"] = q.get("options", [])
                                elif q_type == "slider_labels":
                                    entry["options"] = q.get("slider_options", [])
                                form_questions_emp[fn][q_id] = entry

                    for q_id, q_entry in form_questions_emp[fn].items():
                        answer_raw = ev["answers"].get(q_id)
                        if isinstance(answer_raw, dict):
                            answer_raw = (
                                answer_raw.get("rating")
                                or answer_raw.get("choice")
                                or answer_raw.get("text")
                            )
                        if answer_raw is not None and answer_raw != "":
                            q_entry["answers"].append({
                                "evaluatee_name": emp_name,
                                "evaluator_role": ev_role,
                                "answer":         answer_raw,
                            })

                employee_payload = {
                    "campaign_id":   st.session_state.cr_selected_campaign_id,
                    "campaign_name": st.session_state.cr_selected_campaign_name,
                    "forms": {
                        fn: list(qs.values())
                        for fn, qs in form_questions_emp.items()
                    },
                }

                _script_path = os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__),
                        "..", "..", "..",
                        "services", "result_generation", "main.py",
                    )
                )

                with st.spinner("Running AI analysis…"):
                    proc = subprocess.run(
                        [sys.executable, _script_path, json.dumps(employee_payload)],
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )

                if proc.returncode == 0:
                    st.success("✅ Analysis finished.")
                    try:
                        output   = json.loads(proc.stdout)
                        analysis = output.get("results", {}).get(emp_name, {})
                        if not analysis:
                            st.json(output)
                        elif "raw_response" in analysis:
                            st.code(analysis["raw_response"])
                        else:
                            with st.expander("🔍 Raw LLM output (JSON)", expanded=False):
                                st.json(analysis)

                            def _join(val) -> str:
                                """Accept str or list[str] and return a plain string."""
                                if isinstance(val, str):
                                    return val
                                if isinstance(val, list):
                                    return ", ".join(str(v) for v in val)
                                return str(val)

                            strengths = analysis.get("strengths", [])
                            if strengths:
                                st.markdown("**💪 Strengths**")
                                for s in strengths:
                                    comps = _join(s.get("competence", ""))
                                    st.markdown(f"- **{comps}**")
                                    for ev_text in s.get("evidence", []):
                                        st.caption(f"  • {ev_text}")
                            areas = analysis.get("areas_for_improvement", [])
                            if areas:
                                st.markdown("**📈 Areas for Improvement**")
                                for a in areas:
                                    theme = _join(a.get("theme", ""))
                                    st.markdown(f"- **{theme}**")
                                    for ev_text in a.get("evidence", []):
                                        st.caption(f"  • {ev_text}")
                            summary = analysis.get("summary", "")
                            if summary:
                                st.markdown("**📝 Summary**")
                                st.write(summary)
                            conf_level  = analysis.get("confidence_level", "")
                            conf_reason = analysis.get("confidence_reason", "")
                            if conf_level:
                                conf_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf_level, "⚪")
                                st.caption(f"{conf_color} Confidence: **{conf_level}** — {conf_reason}")

                            # ── Export to Excel (fills Config.xlsx template) ──
                            def _build_ai_excel(emp: str, camp: str, ana: dict) -> bytes:
                                # Locate the template relative to this file's location:
                                # src/ui/pages/results/ → up 4 levels → datafiles/
                                _tmpl = os.path.abspath(os.path.join(
                                    os.path.dirname(__file__),
                                    "..", "..", "..", "..",
                                    "datafiles", "Config.xlsx",
                                ))
                                _wb = openpyxl.load_workbook(_tmpl)
                                _ws = _wb.active          # first / active sheet

                                # ── Write to individual cells ─────────────────
                                _ws["A2"]  = emp
                                _ws["B2"]  = camp
                                _ws["A4"]  = ana.get("summary", "")
                                _ws["A5"]  = ana.get("confidence_level", "")
                                _ws["B5"]  = ana.get("confidence_reason", "")

                                # Strengths – starting at row 8
                                _row = 8
                                for _s in ana.get("strengths", []):
                                    _comp = _s.get("competence", "")
                                    _comp = ", ".join(_comp) if isinstance(_comp, list) else str(_comp)
                                    for _ev in _s.get("evidence", []):
                                        _ws[f"A{_row}"] = _comp
                                        _ws[f"B{_row}"] = str(_ev)
                                        _row += 1

                                # Areas for Improvement – starting at row 20
                                _row = 20
                                for _a in ana.get("areas_for_improvement", []):
                                    _theme = _a.get("theme", "")
                                    _theme = ", ".join(_theme) if isinstance(_theme, list) else str(_theme)
                                    for _ev in _a.get("evidence", []):
                                        _ws[f"A{_row}"] = _theme
                                        _ws[f"B{_row}"] = str(_ev)
                                        _row += 1

                                # Save into an in-memory buffer and return bytes
                                _buf = io.BytesIO()
                                _wb.save(_buf)
                                _buf.seek(0)
                                return _buf.getvalue()

                            _xlsx_bytes = _build_ai_excel(
                                emp_name,
                                st.session_state.cr_selected_campaign_name,
                                analysis,
                            )
                            st.download_button(
                                label="⬇️ Export to Excel",
                                data=_xlsx_bytes,
                                file_name=f"ai_analysis_{emp_name.replace(' ', '_')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="btn_export_ai_excel",
                            )
                    except (json.JSONDecodeError, ValueError):
                        st.code(proc.stdout)
                else:
                    st.error("❌ Pipeline returned an error.")
                    with st.expander("Error details"):
                        st.code(proc.stderr or proc.stdout)


# =========================================================
# CAMPAIGN RESULTS VIEW
# =========================================================
else:
    st.title("Campaign Results")

    # Load campaigns
    with db.connection() as conn:
        campaigns = campaign_repo.list_campaigns(conn)
        campaign_options = ["-- Select a campaign --"]
        campaign_dict = {}
        for c in campaigns:
            campaign_options.append(c.name)
            campaign_dict[c.name] = c.id

    # Restore previously selected campaign index
    current_idx = 0
    if (
        st.session_state.cr_selected_campaign_name
        and st.session_state.cr_selected_campaign_name in campaign_options
    ):
        current_idx = campaign_options.index(st.session_state.cr_selected_campaign_name)

    selected_campaign = st.selectbox("Select Campaign", campaign_options, index=current_idx)

    if selected_campaign != "-- Select a campaign --":
        campaign_id = campaign_dict[selected_campaign]
        st.session_state.cr_selected_campaign_id   = campaign_id
        st.session_state.cr_selected_campaign_name = selected_campaign

        with db.connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT oe.id, oe.name, oe.email, oe.org_role_name
                FROM organisation_employees oe
                JOIN employee_groups eg ON oe.id       = eg.employee_id
                JOIN campaign_groups cg ON eg.group_id = cg.group_id
                WHERE cg.campaign_id = %s
                ORDER BY oe.name ASC
            """, (campaign_id,))
            employees = [
                {"id": r[0], "name": r[1], "email": r[2], "role": r[3]}
                for r in cur.fetchall()
            ]
            cur.close()

        st.divider()

        st.metric("Participants", len(employees))

        st.divider()

        if employees:
            for emp in employees:
                with st.container(border=True):
                    col_name, col_role, col_arrow = st.columns([3, 1, 1])
                    with col_name:
                        st.markdown(f"**{emp['name']}**")
                    with col_role:
                        st.caption(emp["role"] if emp["role"] else "No role")
                    with col_arrow:
                        if st.button("→", key=f"btn_{emp['id']}"):
                            st.session_state.cr_view                  = "employee"
                            st.session_state.cr_selected_employee_id   = emp["id"]
                            st.session_state.cr_selected_employee_name = emp["name"]
                            st.rerun()
        else:
            st.info("No participants found for this campaign.")

    else:
        st.session_state.cr_selected_campaign_id   = None
        st.session_state.cr_selected_campaign_name = None
        st.info("Please select a campaign to view participants.")
