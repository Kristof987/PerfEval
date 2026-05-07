import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.common.common import cleanup_on_group_removal, invalidate_after_team_change, set_step_progress
from ui.pages.campaigns.helpers.helpers import get


def render_groups(selected_id):
    st.subheader("Groups")
    st.caption("Group assignment and team creation")
    st.info(
        "**What is a Group?**\n"
        "A Group is a team of employees (for example: Engineering, Sales, HR) that participates in this campaign. "
        "You assign groups to define who is included in evaluation steps."
    )

    if selected_id == "new":
        st.warning("Create the campaign first, then you can assign/create teams.")
        return

    svc = CampaignService()
    campaign_id = int(selected_id)

    all_groups = svc.list_all_groups()
    assigned_groups = svc.list_campaign_groups(campaign_id)
    assigned_group_ids = {int(get(g, "id", 0) or 0) for g in assigned_groups}

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Create / manage groups", use_container_width=True, key="stepper_open_team_create"):
            st.switch_page("ui/pages/organisation/org_info_page.py")
    with c2:
        if st.button("Continue to Forms", type="primary", use_container_width=True, key="stepper_teams_continue"):
            set_step_progress(selected_id, completed_phase=1, current_phase=2)
            st.rerun()

    st.write("**Assigned Groups:**")
    if assigned_groups:
        for group in assigned_groups:
            group_id = int(get(group, "id", 0) or 0)
            if group_id <= 0:
                continue
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{ICONS.get('office', '🏢')} **{get(group, 'name', 'Unnamed group')}**")
            with col2:
                if st.button(ICONS.get("close", "✖"), key=f"stepper_remove_group_{campaign_id}_{group_id}",
                             use_container_width=True):
                    cleanup_on_group_removal(campaign_id, group_id)
                    invalidate_after_team_change(selected_id)
                    st.rerun()
    else:
        st.info("No teams assigned yet.")

    st.write("---")
    st.write("**Available Groups:**")
    unassigned_groups = [
        g for g in all_groups if int(get(g, "id", 0) or 0) not in assigned_group_ids and int(get(g, "id", 0) or 0) > 0
    ]

    if unassigned_groups:
        for group in unassigned_groups:
            group_id = int(get(group, "id", 0) or 0)
            if group_id <= 0:
                continue
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{ICONS.get('office', '🏢')} {get(group, 'name', 'Unnamed group')}")
            with col2:
                if st.button(
                        f"{ICONS.get('add', '+')} Add",
                        key=f"stepper_add_group_{campaign_id}_{group_id}",
                        use_container_width=True,
                ):
                    svc.assign_group_to_campaign(campaign_id, group_id)
                    invalidate_after_team_change(selected_id)
                    st.rerun()
    else:
        st.info("All teams are already assigned.")
