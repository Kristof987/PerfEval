import streamlit as st

from services.user_forms_service import create_user_forms_service
from ui.pages.employee.assigned_forms_view import render_assigned_forms
from ui.pages.employee.evaluation_form_view import render_selected_evaluation_form
from ui.pages.employee.forms_state import (
    find_selected_evaluation,
    get_current_employee_id_or_stop,
    init_forms_state,
)


service = create_user_forms_service()


def render_page():
    st.header("Forms")
    st.write("View and complete your assigned evaluation forms.")

    employee_id = get_current_employee_id_or_stop()
    init_forms_state()

    evaluations = service.get_user_evaluations(employee_id)
    if not evaluations:
        st.info("No assigned forms found.")
        st.stop()

    render_assigned_forms(evaluations)

    selected_evaluation = find_selected_evaluation(evaluations)
    if selected_evaluation:
        render_selected_evaluation_form(service, selected_evaluation)


render_page()
