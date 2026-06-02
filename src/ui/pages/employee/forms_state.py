import streamlit as st
import streamlit.components.v1 as components


def get_current_employee_id_or_stop():
    employee_id = st.session_state.get("employee_id")
    if not employee_id:
        st.error("No employee is linked to your account. Please contact an administrator.")
        st.stop()
    return employee_id


def init_forms_state():
    if "current_evaluation_id" not in st.session_state:
        st.session_state.current_evaluation_id = None


def find_selected_evaluation(evaluations):
    if not st.session_state.current_evaluation_id:
        return None

    for evaluation in evaluations:
        if evaluation["evaluation_id"] == st.session_state.current_evaluation_id:
            return evaluation
    return None


def render_scroll_anchor(selected_evaluation):
    form_anchor_id = f"eval_form_{selected_evaluation['evaluation_id']}"
    st.markdown(f"<div id='{form_anchor_id}'></div>", unsafe_allow_html=True)
    if st.session_state.get("forms_scroll_to") != form_anchor_id:
        return

    components.html(
        f"""
        <script>
          const jump = () => {{
            const el = window.parent.document.getElementById('{form_anchor_id}');
            if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
          }};
          setTimeout(jump, 80);
        </script>
        """,
        height=0,
    )
    st.session_state["forms_scroll_to"] = None
