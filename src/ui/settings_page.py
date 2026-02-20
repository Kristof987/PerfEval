import streamlit as st
from database.connection import get_connection
from consts.consts import ROLES

st.title("Settings")

# Check if user is Admin
if st.session_state.role == "Admin":
    # Create tabs for Admin users
    tab1, tab2 = st.tabs(["Personal Information", "Organisation Information"])
    
    with tab1:
        st.subheader("Personal Information")
        name = st.text_input("Name", value=st.session_state.name, key="personal_name")
        role = st.selectbox("Choose your role", ROLES, index=ROLES.index(st.session_state.role), key="personal_role")
        email = st.text_input("Email", value=st.session_state.email, key="personal_email")
    
    with tab2:
        st.subheader("Organisation Information")
        
        # Create sub-tabs for Groups and Employees
        sub_tab1, sub_tab2 = st.tabs(["Groups", "Employees"])
        
        # ==================== GROUPS TAB ====================
        with sub_tab1:
            st.subheader("Manage Groups")
            
            # Create new group section
            with st.expander("➕ Create New Group", expanded=False):
                new_group_name = st.text_input("Group Name", key="new_group_name")
                new_group_description = st.text_area("Description", key="new_group_description")
                
                if st.button("Create Group", key="create_group_btn"):
                    if new_group_name:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO organisation_groups (name, description) VALUES (%s, %s)",
                                (new_group_name, new_group_description)
                            )
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success(f"✅ Group '{new_group_name}' created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating group: {e}")
                    else:
                        st.warning("Please enter a group name.")
            
            st.write("---")
            
            # Display existing groups
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description 
                    FROM organisation_groups 
                    ORDER BY name
                """)
                groups = cursor.fetchall()
                cursor.close()
                conn.close()
                
                if groups:
                    st.write(f"**Total Groups:** {len(groups)}")
                    
                    for group_id, group_name, group_description in groups:
                        with st.expander(f"🔹 {group_name}", expanded=False):
                            # Get group members
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT e.id, e.name, e.email
                                FROM organisation_employees e
                                JOIN employee_groups eg ON e.id = eg.employee_id
                                WHERE eg.group_id = %s
                                ORDER BY e.name
                            """, (group_id,))
                            members = cursor.fetchall()
                            cursor.close()
                            conn.close()
                            
                            # Display group description
                            st.write("**Description:**")
                            edited_description = st.text_area(
                                "Description", 
                                value=group_description or "", 
                                key=f"desc_{group_id}",
                                label_visibility="collapsed"
                            )
                            
                            if st.button("Update Description", key=f"update_desc_{group_id}"):
                                try:
                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        "UPDATE organisation_groups SET description = %s WHERE id = %s",
                                        (edited_description, group_id)
                                    )
                                    conn.commit()
                                    cursor.close()
                                    conn.close()
                                    st.success("✅ Description updated!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating description: {e}")
                            
                            st.write("---")
                            st.write(f"**Members ({len(members)}):**")
                            
                            if members:
                                for emp_id, emp_name, emp_email in members:
                                    col1, col2 = st.columns([4, 1])
                                    with col1:
                                        st.write(f"• {emp_name} ({emp_email})")
                                    with col2:
                                        if st.button("Remove", key=f"remove_{group_id}_{emp_id}"):
                                            try:
                                                conn = get_connection()
                                                cursor = conn.cursor()
                                                cursor.execute(
                                                    "DELETE FROM employee_groups WHERE group_id = %s AND employee_id = %s",
                                                    (group_id, emp_id)
                                                )
                                                conn.commit()
                                                cursor.close()
                                                conn.close()
                                                st.success(f"✅ Removed {emp_name} from group!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error removing member: {e}")
                            else:
                                st.info("No members in this group yet.")
                            
                            st.write("---")
                            st.write("**Add Member to Group:**")
                            
                            # Get all employees not in this group
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT e.id, e.name, e.email
                                FROM organisation_employees e
                                WHERE e.id NOT IN (
                                    SELECT employee_id 
                                    FROM employee_groups 
                                    WHERE group_id = %s
                                )
                                ORDER BY e.name
                            """, (group_id,))
                            available_employees = cursor.fetchall()
                            cursor.close()
                            conn.close()
                            
                            if available_employees:
                                employee_options = {f"{name} ({email})": emp_id for emp_id, name, email in available_employees}
                                selected_employee = st.selectbox(
                                    "Select Employee",
                                    options=list(employee_options.keys()),
                                    key=f"add_member_{group_id}"
                                )
                                
                                if st.button("Add Member", key=f"add_btn_{group_id}"):
                                    try:
                                        employee_id = employee_options[selected_employee]
                                        conn = get_connection()
                                        cursor = conn.cursor()
                                        cursor.execute(
                                            "INSERT INTO employee_groups (employee_id, group_id) VALUES (%s, %s)",
                                            (employee_id, group_id)
                                        )
                                        conn.commit()
                                        cursor.close()
                                        conn.close()
                                        st.success(f"✅ Added {selected_employee} to {group_name}!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error adding member: {e}")
                            else:
                                st.info("All employees are already in this group.")
                            
                            st.write("---")
                            # Delete group button
                            if st.button(f"🗑️ Delete Group", key=f"delete_group_{group_id}"):
                                try:
                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    # The foreign key constraint will cascade delete employee_groups entries
                                    cursor.execute("DELETE FROM organisation_groups WHERE id = %s", (group_id,))
                                    conn.commit()
                                    cursor.close()
                                    conn.close()
                                    st.success(f"✅ Group '{group_name}' deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting group: {e}")
                else:
                    st.info("No groups found. Create your first group above!")
                    
            except Exception as e:
                st.error(f"Error loading groups: {e}")
        
        # ==================== EMPLOYEES TAB ====================
        with sub_tab2:
            st.subheader("Manage Employees")
            
            # Create new employee section
            with st.expander("➕ Create New Employee", expanded=False):
                new_emp_name = st.text_input("Employee Name", key="new_emp_name")
                new_emp_email = st.text_input("Employee Email", key="new_emp_email")
                new_emp_role = st.text_input("Employee Role (optional)", key="new_emp_role")
                
                if st.button("Create Employee", key="create_employee_btn"):
                    if new_emp_name and new_emp_email:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO organisation_employees (name, email, org_role_name2) VALUES (%s, %s, %s)",
                                (new_emp_name, new_emp_email, new_emp_role if new_emp_role else None)
                            )
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success(f"✅ Employee '{new_emp_name}' created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating employee: {e}")
                    else:
                        st.warning("Please enter employee name and email.")
            
            st.write("---")
            
            # Display employees
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, email, org_role_name2
                    FROM organisation_employees
                    ORDER BY name
                """)
                employees = cursor.fetchall()
                cursor.close()
                conn.close()
                
                if employees:
                    st.write(f"**Total Employees:** {len(employees)}")
                    
                    for emp_id, emp_name, emp_email, emp_role in employees:
                        with st.expander(f"👤 {emp_name}", expanded=False):
                            st.write(f"**Email:** {emp_email}")
                            st.write(f"**Role:** {emp_role or 'Not specified'}")
                            
                            # Get employee's groups
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT g.id, g.name
                                FROM organisation_groups g
                                JOIN employee_groups eg ON g.id = eg.group_id
                                WHERE eg.employee_id = %s
                                ORDER BY g.name
                            """, (emp_id,))
                            employee_groups = cursor.fetchall()
                            cursor.close()
                            conn.close()
                            
                            st.write("---")
                            st.write(f"**Group Memberships ({len(employee_groups)}):**")
                            
                            if employee_groups:
                                for grp_id, grp_name in employee_groups:
                                    col1, col2 = st.columns([4, 1])
                                    with col1:
                                        st.write(f"• {grp_name}")
                                    with col2:
                                        if st.button("Remove", key=f"emp_remove_{emp_id}_{grp_id}"):
                                            try:
                                                conn = get_connection()
                                                cursor = conn.cursor()
                                                cursor.execute(
                                                    "DELETE FROM employee_groups WHERE employee_id = %s AND group_id = %s",
                                                    (emp_id, grp_id)
                                                )
                                                conn.commit()
                                                cursor.close()
                                                conn.close()
                                                st.success(f"✅ Removed {emp_name} from {grp_name}!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error removing from group: {e}")
                            else:
                                st.info("Not a member of any group yet.")
                            
                            st.write("---")
                            st.write("**Add to Group:**")
                            
                            # Get all groups this employee is not in
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT g.id, g.name
                                FROM organisation_groups g
                                WHERE g.id NOT IN (
                                    SELECT group_id 
                                    FROM employee_groups 
                                    WHERE employee_id = %s
                                )
                                ORDER BY g.name
                            """, (emp_id,))
                            available_groups = cursor.fetchall()
                            cursor.close()
                            conn.close()
                            
                            if available_groups:
                                group_options = {name: grp_id for grp_id, name in available_groups}
                                selected_group = st.selectbox(
                                    "Select Group",
                                    options=list(group_options.keys()),
                                    key=f"add_group_{emp_id}"
                                )
                                
                                if st.button("Add to Group", key=f"add_group_btn_{emp_id}"):
                                    try:
                                        group_id = group_options[selected_group]
                                        conn = get_connection()
                                        cursor = conn.cursor()
                                        cursor.execute(
                                            "INSERT INTO employee_groups (employee_id, group_id) VALUES (%s, %s)",
                                            (emp_id, group_id)
                                        )
                                        conn.commit()
                                        cursor.close()
                                        conn.close()
                                        st.success(f"✅ Added {emp_name} to {selected_group}!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error adding to group: {e}")
                            else:
                                st.info("Already a member of all available groups.")
                else:
                    st.info("No employees found in the database.")
                    
            except Exception as e:
                st.error(f"Error loading employees: {e}")

else:
    # For non-Admin users, show only personal information
    name = st.text_input("Name", value=st.session_state.name)
    role = st.selectbox("Choose your role", ROLES, index=ROLES.index(st.session_state.role))
    email = st.text_input("Email", value=st.session_state.email)
