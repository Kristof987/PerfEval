from collections.abc import Callable
from typing import Any

import streamlit as st

from persistence.db.connection import get_db
from persistence.repository.groups_repo import GroupsRepository
from services.groups_service import GroupsService


AVAILABLE_GROUP_PREVIEW_LIMIT = 5


def create_groups_service() -> GroupsService:
    return GroupsService(get_db(), GroupsRepository())


def group_action_key(action: str, group_id: int) -> str:
    return f"group_{action}_{group_id}"


def format_joined_at(joined_at: Any) -> str:
    if not joined_at:
        return ""

    try:
        return joined_at.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(joined_at)


def load_current_employee_or_stop(service: GroupsService):
    email = st.session_state.get("email")
    if not email:
        st.warning("⚠️ You are not logged in.")
        st.stop()

    try:
        employee = service.get_current_employee(email)
    except Exception as e:
        st.error(f"Error fetching user data: {e}")
        st.stop()

    if not employee:
        st.warning("⚠️ Your employee profile was not found. Please contact an administrator.")
        st.stop()

    return employee


def load_view_or_stop(load_fn: Callable[[], Any], error_message: str):
    try:
        return load_fn()
    except Exception as e:
        st.error(f"{error_message}: {e}")
        st.stop()


def render_group_description(group) -> None:
    if group.description:
        st.write(f"**Description:** {group.description}")
    else:
        st.info("No description available.")


def render_members_list(members: list[tuple[str, str]], total_count: int | None = None) -> None:
    member_count = total_count if total_count is not None else len(members)
    st.write(f"**Members ({member_count}):**")
    for name, mail in members:
        st.write(f"• {name} ({mail})")

    if total_count is not None and total_count > len(members):
        st.write(f"... and {total_count - len(members)} more")


def handle_group_membership_action(
    *,
    button_label: str,
    button_key: str,
    action: Callable[[], None],
    success_message: str,
    error_prefix: str,
) -> None:
    if not st.button(button_label, key=button_key):
        return

    try:
        action()
        st.success(success_message)
        st.rerun()
    except Exception as e:
        st.error(f"{error_prefix}: {e}")


def render_group_action_button(
    *,
    action_name: str,
    group,
    button_label: str,
    action: Callable[[], None],
    success_message: str,
    error_prefix: str,
) -> None:
    st.divider()
    handle_group_membership_action(
        button_label=button_label,
        button_key=group_action_key(action_name, group.id),
        action=action,
        success_message=success_message,
        error_prefix=error_prefix,
    )


def render_my_group_card(service: GroupsService, employee_id: int, group, members: list[tuple[str, str]]) -> None:
    with st.expander(f"🔹 {group.name}", expanded=False):
        render_group_description(group)

        joined_at = format_joined_at(group.joined_at)
        if joined_at:
            st.write(f"**Joined:** {joined_at}")

        st.divider()
        render_members_list(members)

        render_group_action_button(
            action_name="leave",
            group=group,
            button_label=f"Leave {group.name}",
            action=lambda: service.leave_group(employee_id, group.id),
            success_message=f"✅ You have left {group.name}!",
            error_prefix="Error leaving group",
        )


def render_available_group_card(service: GroupsService, employee_id: int, group, preview_members: list[tuple[str, str]]) -> None:
    with st.expander(f"🔹 {group.name} ({group.member_count} members)", expanded=False):
        render_group_description(group)

        if preview_members:
            st.divider()
            render_members_list(preview_members, total_count=group.member_count)
        else:
            st.info("No members yet.")

        render_group_action_button(
            action_name="join",
            group=group,
            button_label=f"Join {group.name}",
            action=lambda: service.join_group(employee_id, group.id),
            success_message=f"✅ You have joined {group.name}!",
            error_prefix="Error joining group",
        )


def render_my_groups_tab(service: GroupsService, employee_id: int) -> None:
    st.subheader("Groups You're In")

    view = load_view_or_stop(
        lambda: service.get_my_groups_view(employee_id),
        "Error loading your groups",
    )

    if not view.groups:
        st.info("📋 You are not currently a member of any groups. Check the 'Available Groups' tab to join one!")
        return

    st.write(f"**You are a member of {len(view.groups)} group(s):**")
    st.write("")

    for group in view.groups:
        members = view.members_by_group.get(group.id, [])
        render_my_group_card(service, employee_id, group, members)


def render_available_groups_tab(service: GroupsService, employee_id: int) -> None:
    st.subheader("Join Groups")
    st.write("Browse and join groups that interest you.")
    st.write("")

    view = load_view_or_stop(
        lambda: service.get_available_groups_view(employee_id, preview_limit=AVAILABLE_GROUP_PREVIEW_LIMIT),
        "Error loading available groups",
    )

    if not view.groups:
        st.info("🎉 You are already a member of all available groups!")
        return

    st.write(f"**{len(view.groups)} group(s) available to join:**")
    st.write("")

    for group in view.groups:
        preview_members = view.preview_members_by_group.get(group.id, [])
        render_available_group_card(service, employee_id, group, preview_members)


def render_my_groups_page() -> None:
    st.title("My Groups")

    service = create_groups_service()
    employee = load_current_employee_or_stop(service)

    tab_my_groups, tab_available_groups = st.tabs(["My Groups", "Available Groups"])

    with tab_my_groups:
        render_my_groups_tab(service, employee.id)

    with tab_available_groups:
        render_available_groups_tab(service, employee.id)


render_my_groups_page()
