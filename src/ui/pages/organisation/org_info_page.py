from collections.abc import Callable
from typing import Any
import time

import streamlit as st

from persistence.repository.org_employees_repo import OrgEmployeesRepository
from persistence.repository.org_groups_repo import OrgGroupsRepository
from persistence.repository.system_roles_repo import SystemRolesRepository
from services.org_admin_service import OrgAdminService
from ui.pages.organisation.org_info_styles import FLASH_HIDE_ALERTS_SCRIPT


FLASH_SUCCESS_KEY = "org_info_success_message"
FLASH_DURATION_SECONDS = 3.5


def create_org_admin_service() -> OrgAdminService:
    return OrgAdminService(
        groups_repo=OrgGroupsRepository(),
        employees_repo=OrgEmployeesRepository(),
        roles_repo=SystemRolesRepository(),
    )


def org_key(*parts: object) -> str:
    return "_".join(str(part) for part in parts)


def render_flash_success() -> None:
    flash_payload = st.session_state.get(FLASH_SUCCESS_KEY)
    if not isinstance(flash_payload, dict):
        return

    message = flash_payload.get("message", "")
    expires_at = float(flash_payload.get("expires_at", 0))
    if message and time.time() <= expires_at:
        st.success(message)
        st.markdown(FLASH_HIDE_ALERTS_SCRIPT, unsafe_allow_html=True)

    st.session_state.pop(FLASH_SUCCESS_KEY, None)


def flash_success_and_rerun(message: str) -> None:
    st.session_state[FLASH_SUCCESS_KEY] = {
        "message": message,
        "expires_at": time.time() + FLASH_DURATION_SECONDS,
    }
    st.rerun()


def load_or_default(load_fn: Callable[[], Any], error_prefix: str, default: Any):
    try:
        return load_fn()
    except Exception as e:
        st.error(f"{error_prefix}: {e}")
        return default


def load_or_stop(load_fn: Callable[[], Any], error_prefix: str):
    try:
        return load_fn()
    except Exception as e:
        st.error(f"{error_prefix}: {e}")
        st.stop()


def handle_org_action(
    *,
    button_label: str,
    key: str,
    action: Callable[[], Any],
    success_message: str | Callable[[Any], str],
    error_prefix: str,
) -> None:
    if not st.button(button_label, key=key):
        return

    try:
        result = action()
        message = success_message(result) if callable(success_message) else success_message
        flash_success_and_rerun(message)
    except Exception as e:
        st.error(f"{error_prefix}: {e}")


def execute_org_action(
    *,
    action: Callable[[], Any],
    success_message: str | Callable[[Any], str],
    error_prefix: str,
) -> None:
    try:
        result = action()
        message = success_message(result) if callable(success_message) else success_message
        flash_success_and_rerun(message)
    except Exception as e:
        st.error(f"{error_prefix}: {e}")


def render_create_group_expander(service: OrgAdminService) -> None:
    with st.expander("➕ Create New Group", expanded=False):
        new_group_name = st.text_input("Group Name", key=org_key("new_group_name"))
        new_group_description = st.text_area("Description", key=org_key("new_group_description"))

        if st.button("Create Group", key=org_key("create_group_btn")):
            if not new_group_name:
                st.warning("Please enter a group name.")
                return

            execute_org_action(
                action=lambda: service.create_group(new_group_name, new_group_description),
                success_message="✅ Group created!",
                error_prefix="Error creating group",
            )


def render_group_description_editor(service: OrgAdminService, group) -> None:
    st.write("**Description:**")
    edited_description = st.text_area(
        "Description",
        value=group.description or "",
        key=org_key("desc", group.id),
        label_visibility="collapsed",
    )

    handle_org_action(
        button_label="Update Description",
        key=org_key("update_desc", group.id),
        action=lambda: service.update_group_description(group.id, edited_description),
        success_message=f"✅ Updated description for {group.name}!",
        error_prefix="Error updating description",
    )


def render_group_members(service: OrgAdminService, group) -> None:
    members = load_or_default(lambda: service.get_group_members(group.id), "Error loading members", [])

    st.write(f"**Members ({len(members)}):**")
    if not members:
        st.info("No members in this group yet.")
        return

    for emp_id, emp_name, emp_email in members:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"• {emp_name} ({emp_email})")
        with col2:
            handle_org_action(
                button_label="Remove",
                key=org_key("remove", group.id, emp_id),
                action=lambda group_id=group.id, employee_id=emp_id: service.remove_member_from_group(group_id, employee_id),
                success_message=f"✅ Removed {emp_name} from {group.name}!",
                error_prefix="Error removing member",
            )


def render_add_group_member(service: OrgAdminService, group) -> None:
    st.write("**Add Member to Group:**")
    available_employees = load_or_default(
        lambda: service.get_employees_not_in_group(group.id),
        "Error loading available employees",
        [],
    )

    if not available_employees:
        st.info("All employees are already in this group.")
        return

    employee_options = {f"{name} ({email})": emp_id for emp_id, name, email in available_employees}
    selected_employee = st.selectbox(
        "Select Employee",
        options=list(employee_options.keys()),
        key=org_key("add_member", group.id),
    )

    handle_org_action(
        button_label="Add Member",
        key=org_key("add_btn", group.id),
        action=lambda: service.add_member_to_group(group.id, employee_options[selected_employee]),
        success_message=f"✅ Added {selected_employee} to {group.name}!",
        error_prefix="Error adding member",
    )


def render_delete_group_button(service: OrgAdminService, group) -> None:
    handle_org_action(
        button_label="🗑️ Delete Group",
        key=org_key("delete_group", group.id),
        action=lambda: service.delete_group(group.id),
        success_message=f"✅ Group '{group.name}' deleted!",
        error_prefix="Error deleting group",
    )


def render_group_card(service: OrgAdminService, group) -> None:
    with st.expander(f"🔹 {group.name}", expanded=False):
        render_group_description_editor(service, group)
        st.divider()
        render_group_members(service, group)
        st.divider()
        render_add_group_member(service, group)
        st.divider()
        render_delete_group_button(service, group)


def render_groups_list(service: OrgAdminService) -> None:
    view = load_or_stop(service.list_groups, "Error loading groups")
    groups = view.groups

    if not groups:
        st.info("No groups found. Create your first group above!")
        return

    st.write(f"**Total Groups:** {len(groups)}")
    for group in groups:
        render_group_card(service, group)


def render_groups_tab(service: OrgAdminService) -> None:
    st.subheader("Manage Groups")
    st.info(
        "**What is a Group?** A Group is a team of employees (for example: Engineering, Sales, HR) "
        "that participates in this campaign. You assign groups to define who is included in evaluation steps."
    )
    st.info(
        "Manage groups here. You can create groups, update descriptions, review members, "
        "and add or remove employees from each group."
    )

    render_create_group_expander(service)
    st.divider()
    render_groups_list(service)


def render_employee_template_download(service: OrgAdminService) -> None:
    template_path = service.get_employee_template_path()
    if not template_path.exists():
        st.info("Employee template not found at datafiles/Employee_Template.xlsx")
        return

    with open(template_path, "rb") as template_file:
        st.download_button(
            label="Download Employee Template",
            data=template_file,
            file_name="Employee_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def render_employee_import_tab(service: OrgAdminService) -> None:
    render_employee_template_download(service)

    uploaded_employee_file = st.file_uploader(
        "Import Employee File",
        type=["xlsx"],
        accept_multiple_files=False,
        key=org_key("import_employee_file"),
    )
    if uploaded_employee_file is None:
        return

    handle_org_action(
        button_label="Import Employees",
        key=org_key("import_employee_btn"),
        action=lambda: service.import_employees(uploaded_employee_file),
        success_message=lambda result: f"✅ Import completed. Added: {result[0]}, skipped: {result[1]}",
        error_prefix="Error importing employees",
    )


def render_system_role_select(service: OrgAdminService) -> int | None:
    roles = service.list_system_roles()
    if not roles:
        st.warning("No system roles available. Create a system role first.")
        return None

    system_role_options = {role.name: role.id for role in roles}
    selected_system_role = st.selectbox(
        "System Role",
        options=list(system_role_options.keys()),
        key=org_key("new_emp_system_role"),
    )
    return system_role_options[selected_system_role]


def render_manual_employee_tab(service: OrgAdminService) -> None:
    st.write("**Add employees manually:**")
    new_emp_name = st.text_input("Employee Name", key=org_key("new_emp_name"))
    new_emp_email = st.text_input("Employee Email", key=org_key("new_emp_email"))
    new_emp_role = st.text_input("Employee Role (optional)", key=org_key("new_emp_role"))
    new_sys_role_id = render_system_role_select(service)

    if not st.button("Create Employee", key=org_key("create_employee_btn")):
        return

    if not (new_emp_name and new_emp_email):
        st.warning("Please enter employee name and email.")
        return

    if new_sys_role_id is None:
        st.warning("Please select a System Role.")
        st.stop()

    execute_org_action(
        action=lambda: service.create_employee(new_emp_name, new_emp_email, new_emp_role, new_sys_role_id),
        success_message=f"✅ Employee '{new_emp_name}' created successfully!",
        error_prefix="Error creating employee",
    )


@st.dialog("Add new employee")
def add_employee_modal(service: OrgAdminService) -> None:
    tab_import, tab_manual = st.tabs(["Import from excel", "Add manually"])

    with tab_import:
        render_employee_import_tab(service)

    with tab_manual:
        render_manual_employee_tab(service)

    if st.button("❌ Cancel", key=org_key("cancel_add_employee")):
        st.rerun()


def render_employee_memberships(service: OrgAdminService, employee) -> None:
    memberships = load_or_default(
        lambda: service.list_employee_groups(employee.id),
        "Error loading memberships",
        [],
    )

    st.divider()
    st.write(f"**Group Memberships ({len(memberships)}):**")
    if not memberships:
        st.info("Not a member of any group yet.")
        return

    for group_id, group_name in memberships:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"• {group_name}")
        with col2:
            handle_org_action(
                button_label="Remove",
                key=org_key("emp_remove", employee.id, group_id),
                action=lambda emp_id=employee.id, grp_id=group_id: service.remove_employee_from_group(emp_id, grp_id),
                success_message=f"✅ Removed {employee.name} from {group_name}!",
                error_prefix="Error removing from group",
            )


def render_add_employee_to_group(service: OrgAdminService, employee) -> None:
    st.divider()
    st.write("**Add to Group:**")
    available_groups = load_or_default(
        lambda: service.list_groups_employee_not_in(employee.id),
        "Error loading available groups",
        [],
    )

    if not available_groups:
        st.info("Already a member of all available groups.")
        return

    group_options = {name: group_id for group_id, name in available_groups}
    selected_group = st.selectbox(
        "Select Group",
        options=list(group_options.keys()),
        key=org_key("add_group", employee.id),
    )
    handle_org_action(
        button_label="Add to Group",
        key=org_key("add_group_btn", employee.id),
        action=lambda: service.add_member_to_group(group_options[selected_group], employee.id),
        success_message=f"✅ Added {employee.name} to {selected_group}!",
        error_prefix="Error adding to group",
    )


def render_employee_card(service: OrgAdminService, employee) -> None:
    with st.expander(f"👤 {employee.name}", expanded=False):
        st.write(f"**Email:** {employee.email}")
        st.write(f"**Role:** {employee.role or 'Not specified'}")
        render_employee_memberships(service, employee)
        render_add_employee_to_group(service, employee)


def render_employees_list(service: OrgAdminService) -> None:
    view = load_or_stop(service.list_employees, "Error loading employees")
    employees = view.employees

    if not employees:
        st.info("No employees found in the database.")
        return

    st.write(f"**Total Employees:** {len(employees)}")
    for employee in employees:
        render_employee_card(service, employee)


def render_employees_tab(service: OrgAdminService) -> None:
    st.subheader("Manage Employees")
    st.info(
        "Manage employee records here. You can add new employees, review details, and maintain their group memberships."
    )

    if st.button("➕ Add new employee", key=org_key("show_add_employee")):
        add_employee_modal(service)

    st.divider()
    render_employees_list(service)


def render_org_info_page() -> None:
    st.subheader("Organisation Information")
    service = create_org_admin_service()
    render_flash_success()

    groups_tab, employees_tab = st.tabs(["Groups", "Employees"])
    with groups_tab:
        render_groups_tab(service)
    with employees_tab:
        render_employees_tab(service)


render_org_info_page()
