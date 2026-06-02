import streamlit as st


DASHBOARD_SELECTED_ID_KEY = "campaign_dashboard_selected_id"
DASHBOARD_PHASE_BY_ID_KEY = "campaign_dashboard_phase_by_id"
DASHBOARD_COMPLETED_PHASE_BY_ID_KEY = "campaign_dashboard_completed_phase_by_id"
DASHBOARD_TEAMS_INVALIDATED_BY_ID_KEY = "campaign_dashboard_teams_invalidated_by_id"


def init_dashboard_state() -> None:
    if DASHBOARD_SELECTED_ID_KEY not in st.session_state:
        st.session_state[DASHBOARD_SELECTED_ID_KEY] = None
    if DASHBOARD_PHASE_BY_ID_KEY not in st.session_state:
        st.session_state[DASHBOARD_PHASE_BY_ID_KEY] = {}
    if DASHBOARD_COMPLETED_PHASE_BY_ID_KEY not in st.session_state:
        st.session_state[DASHBOARD_COMPLETED_PHASE_BY_ID_KEY] = {}
    if DASHBOARD_TEAMS_INVALIDATED_BY_ID_KEY not in st.session_state:
        st.session_state[DASHBOARD_TEAMS_INVALIDATED_BY_ID_KEY] = {}


def select_campaign_and_open(campaign_id) -> None:
    st.session_state[DASHBOARD_SELECTED_ID_KEY] = campaign_id
    st.switch_page("ui/pages/campaigns/campaign_stepper_page.py")


def get_completed_phase(campaign_id: int, default: int = -1) -> int:
    completed_by_id = st.session_state.get(DASHBOARD_COMPLETED_PHASE_BY_ID_KEY, {})
    return int(completed_by_id.get(str(campaign_id), default))


def set_completed_phase(campaign_id: int, completed_phase: int) -> None:
    completed_by_id = st.session_state.get(DASHBOARD_COMPLETED_PHASE_BY_ID_KEY, {})
    completed_by_id[str(campaign_id)] = int(completed_phase)
    st.session_state[DASHBOARD_COMPLETED_PHASE_BY_ID_KEY] = completed_by_id


def is_teams_invalidated(campaign_id: int) -> bool:
    invalidated_by_id = st.session_state.get(DASHBOARD_TEAMS_INVALIDATED_BY_ID_KEY, {})
    return bool(invalidated_by_id.get(str(campaign_id), False))
