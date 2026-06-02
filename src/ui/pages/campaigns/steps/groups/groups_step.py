import streamlit as st

from services.campaign_service import CampaignService
from ui.pages.campaigns.helpers.helpers import get
from ui.pages.campaigns.steps.groups.groups_actions import render_groups_step_actions
from ui.pages.campaigns.steps.groups.groups_lists import render_assigned_groups, render_available_groups
from ui.pages.campaigns.steps.groups.groups_status import (
    render_group_assignment_status,
    render_group_help,
    render_new_campaign_groups_warning,
)


def render_groups(selected_id) -> None:
    st.subheader("Groups")
    st.caption("Group assignment and team creation")

    if selected_id == "new":
        render_new_campaign_groups_warning()
        return

    svc = CampaignService()
    campaign_id = int(selected_id)
    all_groups = svc.list_all_groups()
    assigned_groups = svc.list_campaign_groups(campaign_id)
    assigned_group_ids = {int(get(group, "id", 0) or 0) for group in assigned_groups}

    render_group_assignment_status(len(assigned_groups))
    render_group_help()
    render_groups_step_actions(selected_id)
    render_assigned_groups(selected_id, campaign_id, assigned_groups)
    render_available_groups(svc, selected_id, campaign_id, all_groups, assigned_group_ids)
