import streamlit as st

from database.user_forms import get_user_evaluations, save_evaluation_answers

st.header("Forms")
st.write("View and complete your assigned evaluation forms.")

employee_id = st.session_state.get("employee_id")
if not employee_id:
    st.error("No employee is linked to your account. Please contact an administrator.")
    st.stop()

if "current_evaluation_id" not in st.session_state:
    st.session_state.current_evaluation_id = None

evaluations = get_user_evaluations(employee_id)

if not evaluations:
    st.info("No assigned forms found.")
    st.stop()

campaigns = {}
for evaluation in evaluations:
    campaigns.setdefault(evaluation["campaign_name"], []).append(evaluation)

for campaign_name, items in campaigns.items():
    with st.expander(campaign_name, expanded=False):
        for evaluation in items:
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            with col1:
                st.write(f"**{evaluation['form_name']}**")
                st.caption(evaluation.get("form_description") or "")
            with col2:
                st.write(f"Evaluatee: {evaluation['evaluatee_name']}")
            with col3:
                st.write(evaluation["status"].capitalize())
            with col4:
                st.button(
                    "Fill in",
                    key=f"fill_{evaluation['evaluation_id']}",
                    disabled=evaluation["status"] == "completed",
                    on_click=lambda eval_id=evaluation["evaluation_id"]: st.session_state.update(
                        {"current_evaluation_id": eval_id}
                    ),
                )

selected_evaluation = None
if st.session_state.current_evaluation_id:
    for evaluation in evaluations:
        if evaluation["evaluation_id"] == st.session_state.current_evaluation_id:
            selected_evaluation = evaluation
            break

if selected_evaluation:
    st.write("---")
    st.subheader(
        f"{selected_evaluation['form_name']} — {selected_evaluation['evaluatee_name']}"
    )

    questions = selected_evaluation.get("form_questions") or []
    answers = {}

    with st.form("submit_form"):
        sections = questions.get("sections", [])
        for section in sections:
            for idx, question in enumerate(section.get("questions", [])):
                q_id = question.get("id", idx)
                q_text = question.get("text", "")
                q_type = question.get("type", "Text Response")

                st.write(f"**{idx}. {q_text}**")

                if q_type == "text":
                    answers[q_id] = st.text_area(
                        "Your answer",
                        key=f"answer_{selected_evaluation['evaluation_id']}_{q_id}",
                    )
                elif q_type == "multiple_choice":
                    options = question.get("options", [])
                    answers[q_id] = st.radio(
                        "Select one",
                        options,
                        key=f"answer_{selected_evaluation['evaluation_id']}_{q_id}",
                    )
                elif q_type == "rating":
                    lo = question.get("rating_min", 1)
                    hi = question.get("rating_max", 5)
                    answers[q_id] = st.slider(
                        "Rating",
                        min_value=lo,
                        max_value=hi,
                        value=lo,
                        key=f"answer_{selected_evaluation['evaluation_id']}_{q_id}",
                    )
                elif q_type == "slider_labels":
                    options = question.get("slider_options", [])
                    if options:
                        answers[q_id] = st.select_slider(
                            "Select value",
                            options=options,
                            value=options[0],
                            key=f"answer_{selected_evaluation['evaluation_id']}_{q_id}",
                        )
                elif q_type == "slider_labels":
                    options = question.get("slider_options", [])
                    if options:
                        selected = st.select_slider(
                            "Select value",
                            options=options,
                            value=options[0],
                            key=f"answer_{selected_evaluation['evaluation_id']}_{q_id}",
                        )
                        answers[q_id] = selected

                st.write("")

        submitted = st.form_submit_button("Submit")
        if submitted:
            success = save_evaluation_answers(
                selected_evaluation["evaluation_id"],
                answers,
            )
            if success:
                st.success("Form submitted successfully.")
                st.session_state.current_evaluation_id = None
                st.rerun()
            else:
                st.error("Failed to submit the form.")
