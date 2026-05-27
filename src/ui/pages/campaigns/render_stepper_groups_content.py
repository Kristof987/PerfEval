import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.common.common import cleanup_on_group_removal, invalidate_after_team_change, set_step_progress
from ui.pages.campaigns.helpers.helpers import get


def render_groups(selected_id):
    st.subheader("Groups")
    st.caption("Group assignment and team creation")

    if selected_id == "new":
        st.markdown(
            """
            <div style='border:1px solid #fecaca;background:#fef2f2;color:#991b1b;border-radius:10px;padding:10px 12px;margin:4px 0 10px 0;'>
                <span style='font-size:14px;font-weight:600;'>❌ No groups assigned yet</span><br>
                <span style='font-size:12px;color:#7f1d1d;'>Create the campaign first, then add at least one group to this campaign.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info(
            "**What is a Group?**\n"
            "A Group is a team of employees (for example: Engineering, Sales, HR) that participates in this campaign. "
            "You assign groups to define who is included in evaluation steps."
        )
        st.warning("Create the campaign first, then you can assign/create teams.")
        return

    svc = CampaignService()
    campaign_id = int(selected_id)

    all_groups = svc.list_all_groups()
    assigned_groups = svc.list_campaign_groups(campaign_id)
    assigned_group_ids = {int(get(g, "id", 0) or 0) for g in assigned_groups}

    has_assigned_groups = len(assigned_groups) > 0
    if has_assigned_groups:
        st.markdown(
            f"""
            <div style='border:1px solid #86efac;background:#f0fdf4;color:#166534;border-radius:10px;padding:10px 12px;margin:4px 0 10px 0;'>
                <span style='font-size:14px;font-weight:600;'>✅ Group assignment ready</span><br>
                <span style='font-size:12px;color:#166534;'>{len(assigned_groups)} group(s) already assigned to this campaign.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style='border:1px solid #fecaca;background:#fef2f2;color:#991b1b;border-radius:10px;padding:10px 12px;margin:4px 0 10px 0;'>
                <span style='font-size:14px;font-weight:600;'>❌ No groups assigned yet</span><br>
                <span style='font-size:12px;color:#7f1d1d;'>Add at least one group to this campaign before moving forward.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info(
        "**What is a Group?**\n"
        "A Group is a team of employees (for example: Engineering, Sales, HR) that participates in this campaign. "
        "You assign groups to define who is included in evaluation steps."
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Create / manage groups", use_container_width=True, key="stepper_open_team_create"):
            st.switch_page("ui/pages/organisation/org_info_page.py")
    with c2:
        if st.button("Continue to Forms", type="primary", use_container_width=True, key="stepper_teams_continue"):
            set_step_progress(selected_id, completed_phase=1, current_phase=2)
            st.rerun()

    if assigned_groups:
        st.write("**Assigned Groups:**")
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

    st.write("---")
    st.markdown(
        """
        <style>
            .available-groups-help-wrap { position: relative; display: inline-flex; align-items: center; }
            .available-groups-help-icon {
                display:inline-flex;align-items:center;justify-content:center;
                width:20px;height:20px;border:1px solid #bfdbfe;background:#eff6ff;color:#1d4ed8;
                border-radius:999px;font-size:12px;font-weight:700;line-height:1;
                box-shadow:0 1px 2px rgba(15,23,42,0.08);cursor:default;
            }
            .available-groups-help-tooltip {
                position:absolute;left:50%;transform:translateX(-50%);top:28px;
                min-width:260px;max-width:320px;padding:8px 10px;
                background:#0f172a;color:#f8fafc;border-radius:8px;
                font-size:12px;line-height:1.35;box-shadow:0 6px 20px rgba(15,23,42,0.25);
                opacity:0;visibility:hidden;transition:opacity .14s ease, transform .14s ease;
                pointer-events:none;z-index:20;
            }
            .available-groups-help-wrap:hover .available-groups-help-tooltip {
                opacity:1;visibility:visible;transform:translateX(-50%) translateY(2px);
            }
        </style>
        <div style='display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 0 8px 0;'>
            <div style='display:flex;align-items:center;gap:8px;'>
                <span style='font-size:16px;font-weight:700;color:#0f172a;'>Available Groups</span>
                <span class='available-groups-help-wrap'>
                    <span class='available-groups-help-icon'>?</span>
                    <span class='available-groups-help-tooltip'>Groups listed here are not assigned yet. Click Add to include them in this campaign.</span>
                </span>
            </div>
            <span style='font-size:12px;color:#64748b;'>Hover the ? icon for quick help.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
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
