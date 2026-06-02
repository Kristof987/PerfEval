import streamlit as st


def render_add_system_user_form(service):
    with st.expander("➕ Add New System User", expanded=True):
        with st.form("add_user_form"):
            st.write("Create a new system user who can log into the system.")

            name = st.text_input("Name*", help="Full name of the user")
            username = st.text_input("Username*", help="Login username (will be same as name by default)")
            email = st.text_input("Email*")

            employees = service.list_all_employees()
            employee_id = None
            if employees:
                employee_options = {"None (No linked employee)": None}
                for employee in employees:
                    employee_options[f"{employee['name']} ({employee['email']})"] = employee["id"]
                selected_employee = st.selectbox(
                    "Link to Employee (optional)",
                    options=list(employee_options.keys()),
                    help="Link this system user to an existing employee record",
                )
                employee_id = employee_options[selected_employee]
            else:
                st.info("No employees found. You can still create a system user without linking to an employee.")

            roles = service.list_system_roles()
            if roles:
                role_options = {role["name"]: role["id"] for role in roles}
                selected_role = st.selectbox("System Role*", options=list(role_options.keys()))
                role_id = role_options[selected_role]
            else:
                st.warning("No system roles available. Please create a system role first.")
                role_id = None

            submitted = st.form_submit_button("Create System User")
            if not submitted:
                return

            if not name or not username or not email:
                st.error("Please fill in all required fields (marked with *)")
                return
            if role_id is None:
                st.error("Please select a valid system role")
                return

            final_username = username if username else name
            success, message = service.add_system_user(
                name=name,
                username=final_username,
                email=email,
                sys_szerep_id=role_id,
                current_user_role=st.session_state.role,
                employee_id=employee_id,
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)


def render_add_permission_form(service):
    with st.expander("➕ Add New System Permission"):
        with st.form("add_permission_form"):
            st.write("Create a new system permission.")

            perm_name = st.text_input("Permission Name*")
            perm_desc = st.text_area("Description")
            submitted_perm = st.form_submit_button("Create Permission")
            if not submitted_perm:
                return

            if not perm_name:
                st.error("Please provide a permission name")
                return

            success, message = service.add_system_permission(
                name=perm_name,
                description=perm_desc,
                current_user_role=st.session_state.role,
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)


def render_add_role_form(service):
    with st.expander("➕ Add New System Role"):
        with st.form("add_role_form"):
            st.write("Create a new system role.")

            role_name = st.text_input("Role Name*")
            permissions = service.list_system_permissions()
            if permissions:
                perm_options = {permission["name"]: permission["id"] for permission in permissions}
                perm_options["None"] = None
                selected_perm = st.selectbox("System Permission", options=list(perm_options.keys()))
                perm_id = perm_options[selected_perm]
            else:
                st.info("No permissions available. You can create the role without a permission and assign it later.")
                perm_id = None

            submitted_role = st.form_submit_button("Create Role")
            if not submitted_role:
                return

            if not role_name:
                st.error("Please provide a role name")
                return

            success, message = service.add_system_role(
                name=role_name,
                permission_id=perm_id,
                current_user_role=st.session_state.role,
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
