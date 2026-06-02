import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.helpers.helpers import get
from ui.pages.campaigns.steps.groups.groups_actions import assign_group_to_campaign, remove_group_from_campaign
from ui.pages.campaigns.steps.groups.groups_styles import render_available_groups_header


def render_assigned_groups(selected_id, campaign_id: int, assigned_groups) -> None:
    if not assigned_groups:
        return

    st.write("**Assigned Groups:**")
    for group in assigned_groups:
        render_assigned_group_row(selected_id, campaign_id, group)


def render_assigned_group_row(selected_id, campaign_id: int, group) -> None:
    group_id = int(get(group, "id", 0) or 0)
    if group_id <= 0:
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"{ICONS.get('office', '🏢')} **{get(group, 'name', 'Unnamed group')}**")
    with col2:
        if st.button(
            ICONS.get("close", "✖"),
            key=f"stepper_remove_group_{campaign_id}_{group_id}",
            use_container_width=True,
        ):
            remove_group_from_campaign(selected_id, campaign_id, group_id)


def render_available_groups(svc: CampaignService, selected_id, campaign_id: int, all_groups, assigned_group_ids: set[int]) -> None:
    st.write("---")
    render_available_groups_header()
    unassigned_groups = [
        group
        for group in all_groups
        if int(get(group, "id", 0) or 0) not in assigned_group_ids and int(get(group, "id", 0) or 0) > 0
    ]

    if not unassigned_groups:
        st.info("All teams are already assigned.")
        return

    for group in unassigned_groups:
        render_available_group_row(svc, selected_id, campaign_id, group)


def render_available_group_row(svc: CampaignService, selected_id, campaign_id: int, group) -> None:
    group_id = int(get(group, "id", 0) or 0)
    if group_id <= 0:
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"{ICONS.get('office', '🏢')} {get(group, 'name', 'Unnamed group')}")
    with col2:
        if st.button(
            f"{ICONS.get('add', '+')} Add",
            key=f"stepper_add_group_{campaign_id}_{group_id}",
            use_container_width=True,
        ):
            assign_group_to_campaign(svc, selected_id, campaign_id, group_id)
