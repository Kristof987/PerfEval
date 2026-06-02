import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.steps.forms.forms_selector import render_role_form_selectors
from ui.pages.campaigns.steps.forms.forms_state import initialize_role_form_session_map
from ui.pages.campaigns.steps.forms.forms_table import render_relationship_summary_table
from ui.pages.campaigns.steps.forms.forms_validation import count_selected_pairs, render_assignment_status, save_role_form_defaults
from ui.pages.campaigns.stepper.stepper_state import set_step_progress


def render_forms(selected_id) -> None:
    st.subheader("Forms")
    st.caption("Role-based form assignment")
    status_placeholder = st.empty()
    st.info(
        "Assign a default form for each evaluator → evaluatee role pair. "
        "These defaults are used when creating evaluations in this campaign."
    )
    if st.button("Create / manage forms", use_container_width=True, key="stepper_open_form_builder"):
        st.switch_page("ui/pages/forms/form_builder_page.py")

    if selected_id == "new":
        st.warning("Create the campaign first, then select forms.")
        return

    svc = CampaignService()
    campaign_id = int(selected_id)
    role_names = svc.list_campaign_role_names(campaign_id)
    forms = svc.list_forms()

    if not forms:
        st.error(f"{ICONS['error']} No forms available. Please create an evaluation form first.")
        return

    if not role_names:
        st.error(
            f"{ICONS['error']} No campaign roles available yet. "
            "Assign groups to this campaign and make sure employees have organisation roles."
        )
        return

    form_options = {form["name"]: form["id"] for form in forms}
    form_id_to_name = {form["id"]: form["name"] for form in forms}
    map_key, default_map = initialize_role_form_session_map(
        campaign_id,
        role_names,
        svc.get_role_form_defaults(campaign_id),
    )

    st.write("---")
    render_relationship_summary_table(role_names, st.session_state[map_key], form_id_to_name)
    st.write("---")
    render_role_form_selectors(campaign_id, role_names, st.session_state[map_key], form_options, form_id_to_name)

    total_pairs = len(default_map)
    selected_pairs = count_selected_pairs(st.session_state[map_key])
    render_assignment_status(status_placeholder, selected_pairs, total_pairs)

    st.write("---")
    c_save, c_next = st.columns([1, 1])
    with c_save:
        if st.button(
            "Save form assignments",
            type="primary",
            use_container_width=True,
            key=f"stepper_forms_save_{campaign_id}",
        ):
            save_role_form_defaults(svc, selected_id, campaign_id, st.session_state[map_key])
    with c_next:
        if st.button("Continue to Matrix", use_container_width=True, key=f"stepper_forms_continue_{campaign_id}"):
            set_step_progress(selected_id, current_phase=3)
            st.rerun()
