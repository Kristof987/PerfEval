import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.stepper.stepper_state import set_step_progress
from ui.pages.campaigns.steps.reviewers.reviewers_state import clear_matrix_selection_state


def all_campaign_groups_have_matrix(svc: CampaignService, campaign_id: int) -> bool:
    return svc.all_campaign_groups_have_matrix(campaign_id)


def render_matrix_save_actions(svc: CampaignService, selected_id, campaign_id: int, selected_group_id: int, matrix_key: str) -> None:
    st.write("---")
    c_save, c_reload, c_next = st.columns([1, 1, 1])
    with c_save:
        if st.button(f"{ICONS['save']} Save Matrix", type="primary", use_container_width=True, key=f"stepper_save_{matrix_key}"):
            save_matrix(svc, selected_id, campaign_id, selected_group_id, matrix_key)

    with c_reload:
        if st.button("Reload saved matrix", use_container_width=True, key=f"stepper_reload_{matrix_key}"):
            clear_matrix_selection_state(matrix_key)
            st.rerun()

    with c_next:
        if st.button("Continue to Evaluate", use_container_width=True, key=f"stepper_matrix_continue_{campaign_id}"):
            set_step_progress(selected_id, completed_phase=3, current_phase=4)
            st.rerun()


def save_matrix(svc: CampaignService, selected_id, campaign_id: int, selected_group_id: int, matrix_key: str) -> None:
    assignments = list(st.session_state[matrix_key])
    result = svc.save_evaluations_batch(campaign_id, selected_group_id, assignments, {})

    if not result.success:
        detail = f" Details: {result.error}" if result.error else ""
        st.error(f"{ICONS['error']} Failed to save evaluations.{detail}")
        return

    if all_campaign_groups_have_matrix(svc, campaign_id):
        set_step_progress(selected_id, completed_phase=3, current_phase=4)
    else:
        set_step_progress(selected_id, completed_phase=2, current_phase=4)

    clear_matrix_selection_state(matrix_key)
    st.success(f"{ICONS['check']} Saved {len(assignments)} evaluation assignments.")
    st.rerun()
