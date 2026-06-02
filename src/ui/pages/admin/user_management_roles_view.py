import streamlit as st

from ui.pages.admin.user_management_forms import render_add_role_form


def render_system_roles_tab(service):
    st.subheader("System Roles")

    roles = service.list_system_roles()
    if not roles:
        st.info("No system roles found.")
        return

    for role in roles:
        col1, col2 = st.columns([3, 2])

        with col1:
            st.write(f"**{role['name']}**")

        with col2:
            perm_display = role["permission_name"] if role["permission_name"] else "No permission"
            st.caption(f"Permission: {perm_display}")

        st.divider()


def render_add_system_role_section(service):
    render_add_role_form(service)
