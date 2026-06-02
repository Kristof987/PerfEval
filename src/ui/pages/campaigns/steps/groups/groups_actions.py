import streamlit as st

from services.campaign_service import CampaignService
from ui.pages.campaigns.stepper.group_cleanup import cleanup_on_group_removal
from ui.pages.campaigns.stepper.invalidation import invalidate_after_team_change
from ui.pages.campaigns.stepper.stepper_state import set_step_progress


def render_groups_step_actions(selected_id) -> None:
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Create / manage groups", use_container_width=True, key="stepper_open_team_create"):
            st.switch_page("ui/pages/organisation/org_info_page.py")
    with c2:
        if st.button("Continue to Forms", type="primary", use_container_width=True, key="stepper_teams_continue"):
            set_step_progress(selected_id, completed_phase=1, current_phase=2)
            st.rerun()


def assign_group_to_campaign(svc: CampaignService, selected_id, campaign_id: int, group_id: int) -> None:
    svc.assign_group_to_campaign(campaign_id, group_id)
    invalidate_after_team_change(selected_id)
    st.rerun()


def remove_group_from_campaign(selected_id, campaign_id: int, group_id: int) -> None:
    cleanup_on_group_removal(campaign_id, group_id)
    invalidate_after_team_change(selected_id)
    st.rerun()
