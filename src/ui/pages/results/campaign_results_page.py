import os
import sys
import json
import subprocess
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
            "evaluations": [
                {
                    "evaluation_id":  int,
                    "evaluatee_name": str,
                    "evaluator_name": str,
                    "evaluator_role": str,
                    "form_name":      str,
                    "finish_date":    str | None,
                    "qa_pairs": [
                        {
                            "question_id":   str,
                            "question":      str,
                            "question_type": str,
                            "section":       str,
                            "answer":        any
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT
            e.id,
            eval_tee.name        AS evaluatee_name,
            eval_tor.name        AS evaluator_name,
            eval_tor.org_role_name AS evaluator_role,
            f.id                 AS form_id,
            f.name               AS form_name,
            e.answers,
            e.finish_date,
            f.questions
        FROM evaluation e
        JOIN organisation_employees eval_tee ON e.evaluatee_id = eval_tee.id
        JOIN organisation_employees eval_tor ON e.evaluator_id = eval_tor.id
        JOIN form f ON e.form_id = f.id
        WHERE e.campaign_id = %s
          AND e.status = 'completed'
        ORDER BY eval_tee.name, eval_tor.name
    """, (campaign_id,))

    evaluations = []
    for row in cur.fetchall():
        eval_id        = row[0]
        evaluatee_name = row[1]
        evaluator_name = row[2]
        evaluator_role = row[3] or "Unknown"
        form_name      = row[5]
        answers        = row[6]
        finish_date    = row[7]
        questions_raw  = row[8]

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

        # --- build Q&A pairs ---
        qa_pairs = []
        for section in sections:
            section_title = section.get("title", "General")
            for q in section.get("questions", []):
                if not isinstance(q, dict):
                    continue
                q_id   = str(q.get("id", ""))
                q_text = q.get("text", "")
                q_type = q.get("type", "text")
                answer = answers.get(q_id)

                # Flatten legacy dict-wrapper answers
                if isinstance(answer, dict):
                    if "rating" in answer:
                        answer = answer["rating"]
                    elif "choice" in answer:
                        answer = answer["choice"]
                    elif "text" in answer:
                        answer = answer["text"]

                qa_pairs.append({
                    "question_id":   q_id,
                    "question":      q_text,
                    "question_type": q_type,
                    "section":       section_title,
                    "answer":        answer,
                })

        evaluations.append({
            "evaluation_id":  eval_id,
            "evaluatee_name": evaluatee_name,
            "evaluator_name": evaluator_name,
            "evaluator_role": evaluator_role,
            "form_name":      form_name,
            "finish_date":    str(finish_date) if finish_date else None,
            "qa_pairs":       qa_pairs,
        })

    cur.close()
    return {
        "campaign_id":   campaign_id,
        "campaign_name": campaign_name,
        "evaluations":   evaluations,
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
                eval_tor.name  AS evaluator_name,
                f.id           AS form_id,
                f.name         AS form_name,
                e.answers,
                e.finish_date,
                f.questions
            FROM evaluation e
            JOIN organisation_employees eval_tor ON e.evaluator_id = eval_tor.id
            JOIN form f ON e.form_id = f.id
            WHERE e.evaluatee_id = %s
              AND e.campaign_id  = %s
              AND e.status       = 'completed'
            ORDER BY f.name, eval_tor.name
        """, (employee_id, campaign_id))

        evaluations = []
        for r in cur.fetchall():
            answers = r[4]
            if isinstance(answers, str):
                try:
                    answers = json.loads(answers)
                except (json.JSONDecodeError, ValueError):
                    answers = {}
            elif answers is None:
                answers = {}

            content = _normalize_questions(r[6])

            evaluations.append({
                "id":             r[0],
                "evaluator_name": r[1],
                "form_id":        r[2],
                "form_name":      r[3],
                "answers":        answers,
                "finish_date":    r[5],
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
                st.metric("Evaluations shown", len(filtered_evals))

                # Group by form name
                evals_by_form: dict = {}
                for ev in filtered_evals:
                    evals_by_form.setdefault(ev["form_name"], []).append(ev)

                for form_name, form_evals in evals_by_form.items():
                    st.subheader(f"📋 {form_name}")

                    # Use the first evaluation's sections as the question template
                    # (all evaluations sharing the same form have the same structure)
                    sections = form_evals[0]["sections"] if form_evals else []

                    if not sections:
                        st.caption("_(no questions in this form)_")
                    else:
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
                                    # Collect all answers for this question from every
                                    # evaluation anonymously (no evaluator name shown)
                                    any_answer = False
                                    for ev in form_evals:
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
            # ── Collect section-level rating data ────────────────────────────
            section_ratings: dict = {}   # sec_title -> list of (value, max)

            for ev in evaluations:
                for section in ev["sections"]:
                    sec_title = section.get("title", "General")
                    for q in section.get("questions", []):
                        if not isinstance(q, dict) or q.get("type") != "rating":
                            continue
                        q_id   = str(q.get("id", ""))
                        r_max  = q.get("rating_max", 5)
                        answer = ev["answers"].get(q_id)
                        if answer is None or answer == "":
                            continue
                        # legacy dict wrapper
                        if isinstance(answer, dict):
                            answer = answer.get("rating")
                        if answer is not None:
                            try:
                                section_ratings.setdefault(sec_title, []).append(
                                    (float(answer), float(r_max))
                                )
                            except (ValueError, TypeError):
                                pass

            # Compute per-section averages (normalised to 0–100 %)
            section_names: list = []
            section_avgs:  list = []
            for sec_title, ratings in section_ratings.items():
                if ratings:
                    avg_pct = sum(v / m for v, m in ratings) / len(ratings) * 100
                    section_names.append(sec_title)
                    section_avgs.append(round(avg_pct, 1))

            # ── Layout: two columns ───────────────────────────────────────────
            col_count, col_chart = st.columns([1, 3], gap="medium")

            with col_count:
                with st.container(border=True):
                    st.subheader("Evaluations")
                    st.metric(label="", value=len(evaluations))

            with col_chart:
                with st.container(border=True):
                    st.subheader("Average Rating by Section")
                    if section_names:
                        fig = go.Figure(data=[go.Bar(
                            x=section_names,
                            y=section_avgs,
                            marker_color="#6366f1",
                            text=[f"{v}%" for v in section_avgs],
                            textposition="auto",
                        )])
                        fig.update_layout(
                            yaxis_title="Average (%)",
                            yaxis=dict(range=[0, 100]),
                            xaxis_title="Section",
                            margin=dict(t=10, b=40, l=40, r=40),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No rating questions found in the evaluations.")


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

        # ── AI Result Generation button ──────────────────────────────────
        st.divider()
        st.subheader("🤖 AI Result Generation")

        if st.button(
            "Generate AI Results",
            key="btn_generate_ai_results",
            type="primary",
            help="Collect all completed evaluation answers for this campaign and pass them to the result-generation pipeline.",
        ):
            # 1. Collect campaign Q&A data
            with st.spinner("Collecting campaign evaluation data…"):
                with db.connection() as conn:
                    campaign_payload = get_campaign_qa_json(
                        conn, campaign_id, selected_campaign
                    )

            total_evals  = len(campaign_payload.get("evaluations", []))
            total_qa     = sum(
                len(ev.get("qa_pairs", []))
                for ev in campaign_payload.get("evaluations", [])
            )
            st.info(
                f"Collected **{total_evals}** completed evaluation(s) "
                f"with **{total_qa}** question-answer pair(s)."
            )

            # 2. Locate result_generation/main.py relative to this file
            _script_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),   # …/ui/pages/results/
                    "..", "..", "..",             # → src/
                    "services", "result_generation", "main.py",
                )
            )

            # 3. Call main.py with the JSON payload as argv[1]
            with st.spinner("Running result-generation pipeline…"):
                proc = subprocess.run(
                    [sys.executable, _script_path, json.dumps(campaign_payload)],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

            # 4. Display output
            if proc.returncode == 0:
                st.success("✅ Pipeline finished successfully.")
                try:
                    output = json.loads(proc.stdout)
                    with st.expander("📊 Pipeline output", expanded=True):
                        st.json(output)
                except (json.JSONDecodeError, ValueError):
                    with st.expander("📊 Pipeline output (raw)", expanded=True):
                        st.code(proc.stdout)
            else:
                st.error("❌ Pipeline returned an error.")
                with st.expander("Error details"):
                    st.code(proc.stderr or proc.stdout)

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
