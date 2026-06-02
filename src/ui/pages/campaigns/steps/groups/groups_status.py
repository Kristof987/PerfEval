import streamlit as st

from ui.pages.campaigns.steps.groups.groups_styles import render_status_box


def render_new_campaign_groups_warning() -> None:
    render_status_box(
        success=False,
        title="❌ No groups assigned yet",
        detail="Create the campaign first, then add at least one group to this campaign.",
    )
    st.info(
        "**What is a Group?**\n"
        "A Group is a team of employees (for example: Engineering, Sales, HR) that participates in this campaign. "
        "You assign groups to define who is included in evaluation steps."
    )
    st.warning("Create the campaign first, then you can assign/create teams.")


def render_group_assignment_status(assigned_count: int) -> None:
    if assigned_count > 0:
        render_status_box(
            success=True,
            title="✅ Group assignment ready",
            detail=f"{assigned_count} group(s) already assigned to this campaign.",
        )
    else:
        render_status_box(
            success=False,
            title="❌ No groups assigned yet",
            detail="Add at least one group to this campaign before moving forward.",
        )


def render_group_help() -> None:
    st.info(
        "**What is a Group?**\n"
        "A Group is a team of employees (for example: Engineering, Sales, HR) that participates in this campaign. "
        "You assign groups to define who is included in evaluation steps."
    )
