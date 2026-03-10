import streamlit as st
import json
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

                for ev in form_evals:
                    with st.container(border=True):
                        finish_date = (
                            ev["finish_date"].strftime("%Y-%m-%d")
                            if ev["finish_date"]
                            else "N/A"
                        )
                        st.markdown(
                            f"**Evaluator:** {ev['evaluator_name']} &nbsp;|&nbsp; "
                            f"**Submitted:** {finish_date}"
                        )

                        sections = ev["sections"]
                        answers  = ev["answers"]

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
                                    q_id    = str(q.get("id", ""))
                                    q_text  = q.get("text", "Question")
                                    st.markdown(f"_{q_text}_")
                                    answer = answers.get(q_id)
                                    _render_answer(answer, q)

                st.divider()


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

        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("Participants", len(employees))
        with col2:
            st.subheader("Participants")

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
