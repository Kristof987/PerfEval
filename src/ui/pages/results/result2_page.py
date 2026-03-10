import streamlit as st
import pandas as pd
import plotly.express as px
from consts.consts import ICONS
from persistence.db.connection import get_db
from persistence.repository.evaluation_repo import EvaluationRepository

# -------------------------
# MATERIAL ICONS + CSS
# -------------------------
st.markdown("""
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
.metric-card {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px 20px;
    background: white;
    cursor: pointer;
    transition: all 0.2s ease;
    min-height: 90px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.metric-card:hover {
    border-color: #4A90E2;
    box-shadow: 0 4px 12px rgba(74,144,226,0.2);
    transform: translateY(-2px);
}
.metric-card.active {
    border-color: #4A90E2;
    background: #f0f6ff;
}
.metric-label {
    color: #888;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: #1a1a1a;
}
.material-icons {
    font-size: 18px !important;
    vertical-align: middle;
    color: #4A90E2;
}

/* Streamlit gomb elrejtése — csak a kártyára kattintva aktiválódik */
div[data-testid="stButton"] > button {
    position: absolute;
    opacity: 0;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
    cursor: pointer;
    border: none;
    background: none;
}
.card-wrapper {
    position: relative;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# SESSION STATE
# -------------------------
if "show_submitted_evaluations" not in st.session_state:
    st.session_state.show_submitted_evaluations = False
if "selected_evaluation_id" not in st.session_state:
    st.session_state.selected_evaluation_id = None
if "active_card" not in st.session_state:
    st.session_state.active_card = None

# -------------------------
# REPOSITORY
# -------------------------
repo = EvaluationRepository()
db = get_db()

with db.connection() as conn:
    submitted_evals = repo.list_submitted_evaluations(conn)
    submitted_count = len(submitted_evals)

# -------------------------
# HELPER: kártya renderelés
# -------------------------
def metric_card(icon: str, label: str, value: str, card_key: str) -> bool:
    is_active = st.session_state.active_card == card_key
    active_class = "active" if is_active else ""

    st.markdown(f"""
    <div class="metric-card {active_class}">
        <div class="metric-label">
            <span class="material-icons">{icon}</span>
            {label}
        </div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

    clicked = st.button("click", key=f"btn_{card_key}")
    return clicked

# -------------------------
# METRIKA KÁRTYÁK
# -------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    with st.container():
        st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
        if metric_card("group", "Employees", "198", "employees"):
            st.write("Kattintva!")
            st.switch_page("src/ui/pages/organisation/org_info_page.py")
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
        if metric_card("groups", "Groups", "15", "groups"):
            st.session_state.active_card = "groups" if st.session_state.active_card != "groups" else None
        st.markdown('</div>', unsafe_allow_html=True)

with col3:
    with st.container():
        st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
        if metric_card("task_alt", "Submitted Evaluations", str(submitted_count), "evals"):
            st.session_state.active_card = "evals" if st.session_state.active_card != "evals" else None
            st.session_state.show_submitted_evaluations = (st.session_state.active_card == "evals")
        st.markdown('</div>', unsafe_allow_html=True)

with col4:
    with st.container():
        st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
        if metric_card("schedule", "Avg. Employee Tenure", "4.6 years", "tenure"):
            st.session_state.active_card = "tenure" if st.session_state.active_card != "tenure" else None
        st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# SUBMITTED EVALUATIONS PANEL
# -------------------------
if st.session_state.show_submitted_evaluations:
    st.divider()
    st.subheader(f"{ICONS.get('check', '✅')} Submitted Evaluations")

    if submitted_evals:
        rows = []
        for ev in submitted_evals:
            finish_date = ev.finish_date.strftime('%Y-%m-%d') if ev.finish_date else 'N/A'
            rows.append({
                "ID": ev.id,
                "Evaluator": ev.evaluator_name,
                "Evaluatee": ev.evaluatee_name,
                "Form": ev.form_name,
                "Campaign": ev.campaign_name,
                "Submitted": finish_date
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader(f"{ICONS.get('view', '👁️')} View Evaluation Details")

        eval_options = [f"#{ev.id} - {ev.evaluatee_name} (by {ev.evaluator_name})" for ev in submitted_evals]
        eval_options.insert(0, "-- Select an evaluation --")

        selected_option = st.selectbox("Select evaluation to view:", eval_options, key="eval_selector")

        if selected_option and selected_option != "-- Select an evaluation --":
            selected_id = int(selected_option.split(" - ")[0].replace("#", ""))

            with db.connection() as conn:
                eval_data = repo.get_evaluation_answers(conn, selected_id)

            if eval_data:
                st.markdown(f"**Answers for Evaluation #{selected_id}**")

                questions = eval_data.get("questions", [])
                answers = eval_data.get("answers", {})

                if questions and answers:
                    for q in questions:
                        q_id = str(q.get("id", ""))
                        st.markdown(f"**{q.get('text', 'Question')}:**")
                        answer = answers.get(q_id, "No answer")
                        if isinstance(answer, dict):
                            if "rating" in answer:
                                st.write(f"Rating: {answer['rating']}/5")
                            if "choice" in answer:
                                st.write(f"Choice: {answer['choice']}")
                            if "text" in answer:
                                st.write(f"Text: {answer['text']}")
                        else:
                            st.write(answer)
                        st.divider()
                else:
                    st.info("No answers found for this evaluation.")
    else:
        st.info("No submitted evaluations found.")

# -------------------------
# CHARTS
# -------------------------
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### Employees by Roles")

        role_data = pd.DataFrame({
            "role": ["Employee", "HR Employee", "Trainee", "Team Leader", "Management"],
            "count": [100, 20, 20, 16, 12]
        })

        fig = px.pie(
            role_data,
            values="count",
            names="role",
            hole=0.5
        )
        fig.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    with st.container(border=True):
        st.markdown("### Average Score per Group")

        data = pd.DataFrame({
            "group": [
                "DevOps",
                "Team Leader",
                "Software Tester",
                "Test Automation",
                "Component Tester",
                "Software + Hardware Dev"
            ],
            "score": [8.6, 8.1, 7.2, 6.3, 6.9, 7.7]
        })

        data = data.sort_values("score")

        fig = px.bar(
            data,
            x="score",
            y="group",
            orientation="h"
        )
        fig.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)