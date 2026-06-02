import streamlit as st


def render_system_users_tab(service):
    st.subheader("Current System Users")

    users = service.list_all_system_users()
    if not users:
        st.info("No system users found.")
        return

    for user in users:
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            st.write(f"**{user['name']}** (@{user['username']})")
            st.caption(f"Email: {user['email']}")
            if user["employee_name"]:
                st.caption(f"👤 Linked to employee: {user['employee_name']}")

        with col2:
            role_display = user["role_name"] if user["role_name"] else "No role"
            st.write(f"Role: {role_display}")
            st.caption(f"Created: {user['created_at'].strftime('%Y-%m-%d') if user['created_at'] else 'N/A'}")

        with col3:
            if st.button("Delete", key=f"delete_{user['id']}"):
                success, message = service.delete_system_user(user["id"], st.session_state.role)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        st.divider()
