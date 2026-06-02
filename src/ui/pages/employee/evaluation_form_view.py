import streamlit as st

from ui.pages.employee.forms_state import render_scroll_anchor
from ui.pages.employee.question_inputs import render_question_input


def render_form_section(evaluation_id, section, section_idx, answers):
    section_title = section.get("title", "General")
    section_state_key = f"section_open_{evaluation_id}_{section_idx}"
    if section_state_key not in st.session_state:
        st.session_state[section_state_key] = False

    header_col, toggle_col = st.columns([6, 1])
    with header_col:
        st.markdown(f"**{section_title}**")
    with toggle_col:
        is_open = st.session_state[section_state_key]
        if st.form_submit_button(
            "Hide" if is_open else "Show",
            key=f"toggle_section_{evaluation_id}_{section_idx}",
            type="secondary",
        ):
            st.session_state[section_state_key] = not is_open
            st.rerun()

    if not st.session_state[section_state_key]:
        st.caption("Section is collapsed")
        st.write("")
        return

    for idx, question in enumerate(section.get("questions", [])):
        render_question_input(evaluation_id, question, idx, answers)


def handle_form_submit(service, selected_evaluation, answers):
    success = service.save_evaluation_answers(
        selected_evaluation["evaluation_id"],
        answers,
    )
    if success:
        st.success("Form submitted successfully.")
        st.session_state.current_evaluation_id = None
        st.rerun()
    else:
        st.error("Failed to submit the form.")


def render_selected_evaluation_form(service, selected_evaluation):
    render_scroll_anchor(selected_evaluation)
    st.write("---")
    st.subheader(
        f"{selected_evaluation['form_name']} — {selected_evaluation['evaluatee_name']}"
    )

    questions = service.normalize_questions(selected_evaluation.get("form_questions"))
    answers = {}

    with st.form("submit_form"):
        sections = questions.get("sections", [])
        for section_idx, section in enumerate(sections):
            render_form_section(
                selected_evaluation["evaluation_id"],
                section,
                section_idx,
                answers,
            )

        submitted = st.form_submit_button("Submit")
        if submitted:
            handle_form_submit(service, selected_evaluation, answers)
