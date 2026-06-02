import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.stepper.session_keys import CAMPAIGN_COMPLETED_PHASE_BY_ID_KEY, CAMPAIGN_PHASE_BY_ID_KEY
from ui.pages.campaigns.stepper.stepper_state import set_step_progress


def close_filling_period(service: CampaignService, campaign_id: int) -> None:
    service.close_filling_period(campaign_id)


def advance_to_results_if_needed(selected_id) -> bool:
    phase_key = str(selected_id)
    completed_by_id = st.session_state.get(CAMPAIGN_COMPLETED_PHASE_BY_ID_KEY, {})
    phase_by_id = st.session_state.get(CAMPAIGN_PHASE_BY_ID_KEY, {})
    completed_phase = int(completed_by_id.get(phase_key, -1))
    current_phase = int(phase_by_id.get(phase_key, 0))

    if completed_phase >= 4 and current_phase == 5:
        return False

    set_step_progress(selected_id, completed_phase=4, current_phase=5)
    return True


def render_close_filling_action(service: CampaignService, selected_id, campaign_id: int) -> None:
    if not st.button("Close Form Filling", type="primary", key="stepper_close_filling"):
        return

    try:
        close_filling_period(service, campaign_id)
        advance_to_results_if_needed(selected_id)
        st.success("Filling period closed.")
        st.rerun()
    except Exception as exc:
        st.error(f"{ICONS['error']} Could not close filling period: {exc}")
