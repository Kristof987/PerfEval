import streamlit as st

from ui.pages.admin.user_management_forms import render_add_permission_form


def render_system_permissions_tab(service):
    st.subheader("System Permissions")

    permissions = service.list_system_permissions()
    if not permissions:
        st.info("No system permissions found.")
        return

    for permission in permissions:
        st.write(f"**{permission['name']}**")
        if permission["description"]:
            st.caption(permission["description"])
        st.divider()


def render_add_system_permission_section(service):
    render_add_permission_form(service)
