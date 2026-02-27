import streamlit as st

from database.import_employees import create_employee_and_add_to_system_users
from database.system_users import get_system_roles
from services.org_admin_service import OrgAdminService
from persistence.repository.org_groups_repo import OrgGroupsRepository
from persistence.repository.org_employees_repo import OrgEmployeesRepository
from persistence.repository.system_roles_repo import SystemRolesRepository


st.subheader("Organisation Information")

service = OrgAdminService(
    groups_repo=OrgGroupsRepository(),
    employees_repo=OrgEmployeesRepository(),
    roles_repo=SystemRolesRepository(),
)

sub_tab1, sub_tab2 = st.tabs(["Groups", "Employees"])

with sub_tab1:
    st.subheader("Manage Groups")

    with st.expander("➕ Create New Group", expanded=False):
        new_group_name = st.text_input("Group Name", key="new_group_name")
        new_group_description = st.text_area("Description", key="new_group_description")

        if st.button("Create Group", key="create_group_btn"):
            if not new_group_name:
                st.warning("Please enter a group name.")
            else:
                try:
                    service.create_group(new_group_name, new_group_description)
                    st.success("✅ Group created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating group: {e}")

    st.divider()

    try:
        view = service.list_groups()
        groups = view.groups

        if not groups:
            st.info("No groups found. Create your first group above!")
        else:
            st.write(f"**Total Groups:** {len(groups)}")

            for g in groups:
                with st.expander(f"🔹 {g.name}", expanded=False):

                    st.write("**Description:**")
                    edited_description = st.text_area(
                        "Description",
                        value=g.description or "",
                        key=f"desc_{g.id}",
                        label_visibility="collapsed"
                    )

                    if st.button("Update Description", key=f"update_desc_{g.id}"):
                        try:
                            service.update_group_description(g.id, edited_description)
                            st.success("✅ Updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating description: {e}")

                    st.divider()
                    try:
                        members = service.get_group_members(g.id)
                    except Exception as e:
                        st.error(f"Error loading members: {e}")
                        members = []

                    st.write(f"**Members ({len(members)}):**")
                    if members:
                        for emp_id, emp_name, emp_email in members:
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.write(f"• {emp_name} ({emp_email})")
                            with col2:
                                if st.button("Remove", key=f"remove_{g.id}_{emp_id}"):
                                    try:
                                        service.remove_member_from_group(g.id, emp_id)
                                        st.success(f"✅ Removed {emp_name} from group!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error removing member: {e}")
                    else:
                        st.info("No members in this group yet.")

                    st.divider()
                    st.write("**Add Member to Group:**")
                    try:
                        available_employees = service.get_employees_not_in_group(g.id)
                    except Exception as e:
                        st.error(f"Error loading available employees: {e}")
                        available_employees = []

                    if available_employees:
                        employee_options = {f"{name} ({email})": emp_id for emp_id, name, email in available_employees}
                        selected_employee = st.selectbox(
                            "Select Employee",
                            options=list(employee_options.keys()),
                            key=f"add_member_{g.id}"
                        )

                        if st.button("Add Member", key=f"add_btn_{g.id}"):
                            try:
                                emp_id = employee_options[selected_employee]
                                service.add_member_to_group(g.id, emp_id)
                                st.success(f"✅ Added {selected_employee} to {g.name}!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error adding member: {e}")
                    else:
                        st.info("All employees are already in this group.")

                    st.divider()
                    if st.button("🗑️ Delete Group", key=f"delete_group_{g.id}"):
                        try:
                            service.delete_group(g.id)
                            st.success(f"✅ Group '{g.name}' deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting group: {e}")

    except Exception as e:
        st.error(f"Error loading groups: {e}")


@st.dialog("Add new employee")
def add_employee_modal():
    tab_import, tab_manual = st.tabs(["Import from excel", "Add manually"])

    with tab_import:
        template_path = service.get_employee_template_path()
        if template_path.exists():
            with open(template_path, "rb") as f:
                st.download_button(
                    label="Download Employee Template",
                    data=f,
                    file_name="Employee_Template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        else:
            st.info("Employee template not found at datafiles/Employee_Template.xlsx")

        uploaded_employee_file = st.file_uploader(
            "Import Employee File",
            type=["xlsx"],
            accept_multiple_files=False,
            key="import_employee_file",
        )
        if uploaded_employee_file is not None:
            if st.button("Import Employees", key="import_employee_btn"):
                try:
                    inserted_count, skipped_count = service.import_employees(uploaded_employee_file)
                    st.success(f"✅ Import completed. Added: {inserted_count}, skipped: {skipped_count}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error importing employees: {e}")

    with tab_manual:
        st.write(f"**Add employees manually:**")
        new_emp_name = st.text_input("Employee Name", key="new_emp_name")
        new_emp_email = st.text_input("Employee Email", key="new_emp_email")
        new_emp_role = st.text_input("Employee Role (optional)", key="new_emp_role")
        roles = get_system_roles()
        if roles:
            system_role_options = {role["name"]: role["id"] for role in roles}
            selected_system_role = st.selectbox(
                "System Role",
                options=list(system_role_options.keys()),
                key="new_emp_system_role"
            )
            new_sys_role_id = system_role_options[selected_system_role]
        else:
            st.warning("No system roles available. Create a system role first.")
            new_sys_role_id = None

        if st.button("Create Employee", key="create_employee_btn"):
            if new_emp_name and new_emp_email:
                if new_sys_role_id is None:
                    st.warning("Please select a System Role.")
                    st.stop()
                try:
                    create_employee_and_add_to_system_users(new_emp_name, new_emp_email, new_emp_role, new_sys_role_id)
                    st.success(f"✅ Employee '{new_emp_name}' created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating employee: {e}")
            else:
                st.warning("Please enter employee name and email.")

    # Cancel button to close the add employee section
    if st.button("❌ Cancel", key="cancel_add_employee"):
        st.session_state.show_add_employee = False
        st.rerun()


with sub_tab2:
    st.subheader("Manage Employees")

    # Initialize session state for showing add employee UI
    if "show_add_employee" not in st.session_state:
        st.session_state.show_add_employee = False

    if st.button("➕ Add new employee"):
        st.session_state.show_add_employee = True

    if st.session_state.show_add_employee:
        add_employee_modal()

    st.divider()

    try:
        view = service.list_employees()
        employees = view.employees

        if not employees:
            st.info("No employees found in the database.")
        else:
            st.write(f"**Total Employees:** {len(employees)}")

            for emp in employees:
                with st.expander(f"👤 {emp.name}", expanded=False):
                    st.write(f"**Email:** {emp.email}")
                    st.write(f"**Role:** {emp.role or 'Not specified'}")

                    try:
                        memberships = service.list_employee_groups(emp.id)
                    except Exception as e:
                        st.error(f"Error loading memberships: {e}")
                        memberships = []

                    st.divider()
                    st.write(f"**Group Memberships ({len(memberships)}):**")
                    if memberships:
                        for grp_id, grp_name in memberships:
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.write(f"• {grp_name}")
                            with col2:
                                if st.button("Remove", key=f"emp_remove_{emp.id}_{grp_id}"):
                                    try:
                                        service.remove_employee_from_group(emp.id, grp_id)
                                        st.success(f"✅ Removed {emp.name} from {grp_name}!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error removing from group: {e}")
                    else:
                        st.info("Not a member of any group yet.")

                    st.divider()
                    st.write("**Add to Group:**")
                    try:
                        available_groups = service.list_groups_employee_not_in(emp.id)
                    except Exception as e:
                        st.error(f"Error loading available groups: {e}")
                        available_groups = []

                    if available_groups:
                        group_options = {name: gid for gid, name in available_groups}
                        selected_group = st.selectbox(
                            "Select Group",
                            options=list(group_options.keys()),
                            key=f"add_group_{emp.id}"
                        )
                        if st.button("Add to Group", key=f"add_group_btn_{emp.id}"):
                            try:
                                group_id = group_options[selected_group]
                                service.add_member_to_group(group_id, emp.id)
                                st.success(f"✅ Added {emp.name} to {selected_group}!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error adding to group: {e}")
                    else:
                        st.info("Already a member of all available groups.")

    except Exception as e:
        st.error(f"Error loading employees: {e}")