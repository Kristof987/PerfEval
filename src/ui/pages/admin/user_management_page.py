import streamlit as st
from services.system_user_service import create_system_user_service

service = create_system_user_service()

st.header("User Management")
st.write(f"You are logged in as {st.session_state.role}.")

if st.session_state.role not in ["Admin", "HR employee"]:
    st.error("You don't have permission to access this page.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["System Users", "System Roles", "System Permissions", "Add New"])

with tab1:
    st.subheader("Current System Users")
    
    users = service.list_all_system_users()
    
    if users:
        for user in users:
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{user['name']}** (@{user['username']})")
                st.caption(f"Email: {user['email']}")
                if user['employee_name']:
                    st.caption(f"👤 Linked to employee: {user['employee_name']}")
            
            with col2:
                role_display = user['role_name'] if user['role_name'] else "No role"
                st.write(f"Role: {role_display}")
                st.caption(f"Created: {user['created_at'].strftime('%Y-%m-%d') if user['created_at'] else 'N/A'}")
            
            with col3:
                if st.button("Delete", key=f"delete_{user['id']}"):
                    success, message = service.delete_system_user(user['id'], st.session_state.role)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            
            st.divider()
    else:
        st.info("No system users found.")

with tab2:
    st.subheader("System Roles")
    
    roles = service.list_system_roles()
    
    if roles:
        for role in roles:
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.write(f"**{role['name']}**")
            
            with col2:
                perm_display = role['permission_name'] if role['permission_name'] else "No permission"
                st.caption(f"Permission: {perm_display}")
            
            st.divider()
    else:
        st.info("No system roles found.")

with tab3:
    st.subheader("System Permissions")
    
    permissions = service.list_system_permissions()
    
    if permissions:
        for perm in permissions:
            st.write(f"**{perm['name']}**")
            if perm['description']:
                st.caption(perm['description'])
            st.divider()
    else:
        st.info("No system permissions found.")

with tab4:
    st.subheader("Add New Items")
    
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
                for emp in employees:
                    employee_options[f"{emp['name']} ({emp['email']})"] = emp['id']
                selected_employee = st.selectbox(
                    "Link to Employee (optional)",
                    options=list(employee_options.keys()),
                    help="Link this system user to an existing employee record"
                )
                employee_id = employee_options[selected_employee]
            else:
                st.info("No employees found. You can still create a system user without linking to an employee.")
            
            roles = service.list_system_roles()
            if roles:
                role_options = {role['name']: role['id'] for role in roles}
                selected_role = st.selectbox("System Role*", options=list(role_options.keys()))
                role_id = role_options[selected_role]
            else:
                st.warning("No system roles available. Please create a system role first.")
                role_id = None
            
            submitted = st.form_submit_button("Create System User")
            
            if submitted:
                if not name or not username or not email:
                    st.error("Please fill in all required fields (marked with *)")
                elif role_id is None:
                    st.error("Please select a valid system role")
                else:
                    final_username = username if username else name
                    
                    success, message = service.add_system_user(
                        name=name,
                        username=final_username,
                        email=email,
                        sys_szerep_id=role_id,
                        current_user_role=st.session_state.role,
                        employee_id=employee_id
                    )
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    if st.session_state.role == "Admin":
        with st.expander("➕ Add New System Permission"):
            with st.form("add_permission_form"):
                st.write("Create a new system permission.")
                
                perm_name = st.text_input("Permission Name*")
                perm_desc = st.text_area("Description")
                
                submitted_perm = st.form_submit_button("Create Permission")
                
                if submitted_perm:
                    if not perm_name:
                        st.error("Please provide a permission name")
                    else:
                        success, message = service.add_system_permission(
                            name=perm_name,
                            description=perm_desc,
                            current_user_role=st.session_state.role
                        )
                        
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        
        with st.expander("➕ Add New System Role"):
            with st.form("add_role_form"):
                st.write("Create a new system role.")
                
                role_name = st.text_input("Role Name*")
                
                permissions = service.list_system_permissions()
                if permissions:
                    perm_options = {perm['name']: perm['id'] for perm in permissions}
                    perm_options["None"] = None
                    selected_perm = st.selectbox("System Permission", options=list(perm_options.keys()))
                    perm_id = perm_options[selected_perm]
                else:
                    st.info("No permissions available. You can create the role without a permission and assign it later.")
                    perm_id = None
                
                submitted_role = st.form_submit_button("Create Role")
                
                if submitted_role:
                    if not role_name:
                        st.error("Please provide a role name")
                    else:
                        success, message = service.add_system_role(
                            name=role_name,
                            permission_id=perm_id,
                            current_user_role=st.session_state.role
                        )
                        
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

st.divider()
st.caption("💡 Only Admin and HR employee can manage system users.")
