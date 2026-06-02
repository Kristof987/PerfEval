from dataclasses import dataclass

import streamlit as st

from services.campaign_service import CampaignService
from ui.pages.campaigns.helpers.helpers import count_days_left, datetime_to_string
from ui.pages.campaigns.stepper.session_keys import (
    CAMPAIGN_COMPLETED_PHASE_BY_ID_KEY,
    CAMPAIGN_PHASE_BY_ID_KEY,
    CAMPAIGN_SELECTED_ID_KEY,
    CAMPAIGN_TEAMS_INVALIDATED_BY_ID_KEY,
    STEPPER_LAST_SELECTED_ID_KEY,
    STEPPER_SCROLL_TO_TOP_KEY,
    STEPPER_WIDGET_NONCE_BY_ID_KEY,
    stepper_pills_key,
)
from ui.pages.campaigns.stepper.stepper_progress import max_enabled_phase_for, resolve_completed_phase


@dataclass
class StepperContext:
    selected_id: int | str
    campaign_name: str
    meta_text: str
    selected_campaign: object | None
    phase_key: str
    current_phase: int
    completed_phase: int
    max_enabled_phase: int
    widget_nonce: int


def init_stepper_state() -> None:
    defaults = {
        CAMPAIGN_SELECTED_ID_KEY: None,
        CAMPAIGN_PHASE_BY_ID_KEY: {},
        CAMPAIGN_COMPLETED_PHASE_BY_ID_KEY: {},
        CAMPAIGN_TEAMS_INVALIDATED_BY_ID_KEY: {},
        STEPPER_LAST_SELECTED_ID_KEY: None,
        STEPPER_WIDGET_NONCE_BY_ID_KEY: {},
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def load_selected_campaign_or_stop(selected_id):
    if selected_id == "new":
        return None, "New campaign", "New campaign"

    service = CampaignService()
    try:
        campaigns = service.list_campaigns()
    except Exception as exc:
        st.error(f"Could not load campaign: {exc}")
        st.stop()

    campaign_by_id = {int(getattr(campaign, "id", 0) or 0): campaign for campaign in campaigns}
    selected_campaign = campaign_by_id.get(int(selected_id))
    if selected_campaign is None:
        st.info("Selected campaign no longer exists.")
        st.stop()

    campaign_name = getattr(selected_campaign, "name", "Campaign")
    selected_end_date = getattr(selected_campaign, "end_date", None)
    selected_deadline = datetime_to_string(selected_end_date)
    selected_days_left = count_days_left(selected_end_date)
    meta_text = (
        f"Deadline: {selected_deadline} ({selected_days_left} days)"
        if selected_days_left is not None
        else f"Deadline: {selected_deadline}"
    )
    return selected_campaign, campaign_name, meta_text


def build_stepper_context() -> StepperContext:
    init_stepper_state()
    selected_id = st.session_state[CAMPAIGN_SELECTED_ID_KEY]
    if selected_id is None:
        st.info("No campaign selected.")
        st.stop()

    selected_campaign, campaign_name, meta_text = load_selected_campaign_or_stop(selected_id)
    phase_key = str(selected_id)
    phase_by_id = st.session_state[CAMPAIGN_PHASE_BY_ID_KEY]
    completed_by_id = st.session_state[CAMPAIGN_COMPLETED_PHASE_BY_ID_KEY]

    completed_phase = resolve_completed_phase(selected_id, selected_campaign, completed_by_id)
    st.session_state[CAMPAIGN_COMPLETED_PHASE_BY_ID_KEY] = completed_by_id

    invalidated_by_id = st.session_state.get(CAMPAIGN_TEAMS_INVALIDATED_BY_ID_KEY, {})
    max_enabled_phase = max_enabled_phase_for(selected_id, completed_phase, invalidated_by_id)
    current_phase = int(phase_by_id.get(phase_key, 0))

    last_selected_id = st.session_state.get(STEPPER_LAST_SELECTED_ID_KEY)
    if selected_id != "new" and str(last_selected_id) != phase_key:
        current_phase = max_enabled_phase
        phase_by_id[phase_key] = current_phase

    if current_phase > max_enabled_phase:
        current_phase = max_enabled_phase
        phase_by_id[phase_key] = current_phase

    st.session_state[CAMPAIGN_PHASE_BY_ID_KEY] = phase_by_id
    st.session_state[STEPPER_LAST_SELECTED_ID_KEY] = selected_id

    widget_nonce_by_id = st.session_state.get(STEPPER_WIDGET_NONCE_BY_ID_KEY, {})
    widget_nonce = int(widget_nonce_by_id.get(phase_key, 0))

    return StepperContext(
        selected_id=selected_id,
        campaign_name=campaign_name,
        meta_text=meta_text,
        selected_campaign=selected_campaign,
        phase_key=phase_key,
        current_phase=current_phase,
        completed_phase=completed_phase,
        max_enabled_phase=max_enabled_phase,
        widget_nonce=widget_nonce,
    )


def update_current_phase(phase_key: str, new_phase: int) -> None:
    phase_by_id = st.session_state.get(CAMPAIGN_PHASE_BY_ID_KEY, {})
    phase_by_id[phase_key] = int(new_phase)
    st.session_state[CAMPAIGN_PHASE_BY_ID_KEY] = phase_by_id


def set_step_progress(
    campaign_id,
    completed_phase: int | None = None,
    current_phase: int | None = None,
    force_completed: bool = False,
    scroll_to_top: bool = True,
) -> None:
    if campaign_id == "new" or campaign_id is None:
        return

    phase_key = str(campaign_id)

    completed_by_id = st.session_state.get(CAMPAIGN_COMPLETED_PHASE_BY_ID_KEY, {})
    previous_completed = int(completed_by_id.get(phase_key, -1))
    if completed_phase is not None:
        if force_completed:
            completed_by_id[phase_key] = int(completed_phase)
        else:
            completed_by_id[phase_key] = max(previous_completed, int(completed_phase))
    st.session_state[CAMPAIGN_COMPLETED_PHASE_BY_ID_KEY] = completed_by_id

    if completed_phase is not None and int(completed_phase) >= 2:
        invalidated_by_id = st.session_state.get(CAMPAIGN_TEAMS_INVALIDATED_BY_ID_KEY, {})
        invalidated_by_id[phase_key] = False
        st.session_state[CAMPAIGN_TEAMS_INVALIDATED_BY_ID_KEY] = invalidated_by_id

    if current_phase is not None:
        phase_by_id = st.session_state.get(CAMPAIGN_PHASE_BY_ID_KEY, {})
        phase_by_id[phase_key] = int(current_phase)
        st.session_state[CAMPAIGN_PHASE_BY_ID_KEY] = phase_by_id

        nonce_by_id = st.session_state.get(STEPPER_WIDGET_NONCE_BY_ID_KEY, {})
        nonce_by_id[phase_key] = int(nonce_by_id.get(phase_key, 0)) + 1
        st.session_state[STEPPER_WIDGET_NONCE_BY_ID_KEY] = nonce_by_id

        pills_key = stepper_pills_key(phase_key)
        if pills_key in st.session_state:
            del st.session_state[pills_key]

        if scroll_to_top:
            st.session_state[STEPPER_SCROLL_TO_TOP_KEY] = True
