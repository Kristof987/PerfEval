import streamlit as st
from services.system_user_service import create_system_user_service
from services.system_user_service import ADMIN_ROLE, HR_EMPLOYEE_ROLE
from ui.pages.admin.user_management_forms import render_add_system_user_form
from ui.pages.admin.user_management_permissions_view import (
    render_add_system_permission_section,
    render_system_permissions_tab,
)
from ui.pages.admin.user_management_roles_view import (
    render_add_system_role_section,
    render_system_roles_tab,
)
from ui.pages.admin.user_management_users_view import render_system_users_tab

service = create_system_user_service()


ADMIN_ROLES = [ADMIN_ROLE, HR_EMPLOYEE_ROLE]


def ensure_admin_access():
    st.header("User Management")
    st.write(f"You are logged in as {st.session_state.role}.")

    if st.session_state.role not in ADMIN_ROLES:
        st.error("You don't have permission to access this page.")
        st.stop()


def render_add_new_tab():
    st.subheader("Add New Items")
    render_add_system_user_form(service)

    if st.session_state.role == ADMIN_ROLE:
        render_add_system_permission_section(service)
        render_add_system_role_section(service)


def render_page():
    ensure_admin_access()
    tab_users, tab_roles, tab_permissions, tab_add_new = st.tabs(
        ["System Users", "System Roles", "System Permissions", "Add New"]
    )

    with tab_users:
        render_system_users_tab(service)
    with tab_roles:
        render_system_roles_tab(service)
    with tab_permissions:
        render_system_permissions_tab(service)
    with tab_add_new:
        render_add_new_tab()

    st.divider()
    st.caption("💡 Only Admin and HR employee can manage system users.")


render_page()
