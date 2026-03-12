import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
from consts.consts import ICONS
from persistence.db.connection import get_db
from persistence.repository.evaluation_repo import EvaluationRepository

# Initialize session state for submitted evaluations view
if "show_submitted_evaluations" not in st.session_state:
    st.session_state.show_submitted_evaluations = False
if "selected_evaluation_id" not in st.session_state:
    st.session_state.selected_evaluation_id = None

repo = EvaluationRepository()
db = get_db()

# Get submitted evaluations count
with db.connection() as conn:
    submitted_evals = repo.list_submitted_evaluations(conn)
    submitted_count = len(submitted_evals)

col1, col2, col3, col4 = st.columns(4)

with col1:
    with st.container(border=True):
        st.metric("Employees", "198")

with col2:
    with st.container(border=True):
        st.metric("Groups", "15")

with col3:
    with st.container(border=True):
        st.metric("Submitted evaluations", "230")

with col4:
    with st.container(border=True):
        st.metric("Average Employee Tenure", "4.6 years")

# Show submitted evaluations list if clicked
if st.session_state.show_submitted_evaluations:
    st.divider()
    st.subheader(f"{ICONS.get('check', '✅')} Submitted Evaluations")
    
    if submitted_evals:
        # Create a dataframe for display
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
        
        # Allow selecting an evaluation to view details
        st.subheader(f"{ICONS.get('view', '👁️')} View Evaluation Details")
        
        eval_options = [f"#{ev.id} - {ev.evaluatee_name} (by {ev.evaluator_name})" for ev in submitted_evals]
        eval_options.insert(0, "-- Select an evaluation --")
        
        selected_option = st.selectbox("Select evaluation to view:", eval_options, key="eval_selector")
        
        if selected_option and selected_option != "-- Select an evaluation --":
            # Extract ID from selection
            selected_id = int(selected_option.split(" - ")[0].replace("#", ""))
            
            # Get evaluation details
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
                            # Handle rating/choice answers
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

        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=30, b=10)
        )

        st.plotly_chart(fig, use_container_width=True)

# -------------------------
# BAR CHART CARD
# -------------------------

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

        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=30, b=10)
        )

        st.plotly_chart(fig, use_container_width=True)
