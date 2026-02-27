# import streamlit as st
# from pathlib import Path
#
# from database.import_employees import create_new_organisation_group, list_existing_organisation_groups, \
#     get_group_members, update_organisation_group_description, delete_employee_from_employee_groups, \
#     find_employees_not_part_of_employee_group, add_employee_to_employee_group, delete_employee_group, \
#     import_employees_from_template, create_employee_and_add_to_system_users, get_organisation_employees, \
#     get_employees_group_memberships, remove_employee_from_employee_groups, find_organisation_groups_employee_not_in
# from database.system_users import get_system_roles
#
# st.subheader("Organisation Information")
#
# sub_tab1, sub_tab2 = st.tabs(["Groups", "Employees"])
#
# with sub_tab1:
#     st.subheader("Manage Groups")
#
#     with st.expander("➕ Create New Group", expanded=False):
#         new_group_name = st.text_input("Group Name", key="new_group_name")
#         new_group_description = st.text_area("Description", key="new_group_description")
#
#         if st.button("Create Group", key="create_group_btn"):
#             if new_group_name:
#                 try:
#                     create_new_organisation_group(new_group_name, new_group_description)
#                 except Exception as e:
#                     st.error(f"Error creating group: {e}")
#             else:
#                 st.warning("Please enter a group name.")
#
#     st.write("---")
#
#     # Display existing groups
#     try:
#         groups = list_existing_organisation_groups()
#
#         if groups:
#             st.write(f"**Total Groups:** {len(groups)}")
#
#             for group_id, group_name, group_description in groups:
#                 with st.expander(f"🔹 {group_name}", expanded=False):
#
#                     members = get_group_members(group_id)
#
#                     st.write("**Description:**")
#                     edited_description = st.text_area(
#                         "Description",
#                         value=group_description or "",
#                         key=f"desc_{group_id}",
#                         label_visibility="collapsed"
#                     )
#
#                     if st.button("Update Description", key=f"update_desc_{group_id}"):
#                         try:
#                             update_organisation_group_description(group_id, edited_description)
#                         except Exception as e:
#                             st.error(f"Error updating description: {e}")
#
#                     st.write("---")
#                     st.write(f"**Members ({len(members)}):**")
#
#                     if members:
#                         for emp_id, emp_name, emp_email in members:
#                             col1, col2 = st.columns([4, 1])
#                             with col1:
#                                 st.write(f"• {emp_name} ({emp_email})")
#                             with col2:
#                                 if st.button("Remove", key=f"remove_{group_id}_{emp_id}"):
#                                     try:
#                                         delete_employee_from_employee_groups(group_id, emp_id)
#                                         st.success(f"✅ Removed {emp_name} from group!")
#                                         st.rerun()
#                                     except Exception as e:
#                                         st.error(f"Error removing member: {e}")
#                     else:
#                         st.info("No members in this group yet.")
#
#                     st.write("---")
#                     st.write("**Add Member to Group:**")
#
#                     available_employees = find_employees_not_part_of_employee_group(group_id)
#
#                     if available_employees:
#                         employee_options = {f"{name} ({email})": emp_id for emp_id, name, email in available_employees}
#                         selected_employee = st.selectbox(
#                             "Select Employee",
#                             options=list(employee_options.keys()),
#                             key=f"add_member_{group_id}"
#                         )
#
#                         if st.button("Add Member", key=f"add_btn_{group_id}"):
#                             try:
#                                 employee_id = employee_options[selected_employee]
#                                 add_employee_to_employee_group(employee_id, group_id)
#                                 st.success(f"✅ Added {selected_employee} to {group_name}!")
#                                 st.rerun()
#                             except Exception as e:
#                                 st.error(f"Error adding member: {e}")
#                     else:
#                         st.info("All employees are already in this group.")
#
#                     st.write("---")
#                     if st.button(f"🗑️ Delete Group", key=f"delete_group_{group_id}"):
#                         try:
#                             delete_employee_group(group_id)
#                             st.success(f"✅ Group '{group_name}' deleted!")
#                             st.rerun()
#                         except Exception as e:
#                             st.error(f"Error deleting group: {e}")
#         else:
#             st.info("No groups found. Create your first group above!")
#
#     except Exception as e:
#         st.error(f"Error loading groups: {e}")
#
# with sub_tab2:
#     st.subheader("Manage Employees")
#
#     template_path = Path("datafiles") / "Employee_Template.xlsx"
#     if template_path.exists():
#         with open(template_path, "rb") as template_file:
#             st.download_button(
#                 label="Download Employee Template",
#                 data=template_file,
#                 file_name="Employee_Template.xlsx",
#                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             )
#     else:
#         st.info("Employee template not found at datafiles/Employee_Template.xlsx")
#
#     uploaded_employee_file = st.file_uploader(
#         "Import Employee File",
#         type=["xlsx"],
#         accept_multiple_files=False,
#         key="import_employee_file",
#     )
#     if uploaded_employee_file is not None:
#         if st.button("Import Employees", key="import_employee_btn"):
#             try:
#                 inserted_count, skipped_count = import_employees_from_template(uploaded_employee_file)
#                 st.success(
#                     f"✅ Import completed. Added: {inserted_count}, skipped (already exists or role missing): {skipped_count}"
#                 )
#                 st.rerun()
#             except Exception as e:
#                 st.error(f"Error importing employees: {e}")
#
#     with st.expander("➕ Create New Employee", expanded=False):
#         new_emp_name = st.text_input("Employee Name", key="new_emp_name")
#         new_emp_email = st.text_input("Employee Email", key="new_emp_email")
#         new_emp_role = st.text_input("Employee Role (optional)", key="new_emp_role")
#         roles = get_system_roles()
#         if roles:
#             system_role_options = {role["name"]: role["id"] for role in roles}
#             selected_system_role = st.selectbox(
#                 "System Role",
#                 options=list(system_role_options.keys()),
#                 key="new_emp_system_role"
#             )
#             new_sys_role_id = system_role_options[selected_system_role]
#         else:
#             st.warning("No system roles available. Create a system role first.")
#             new_sys_role_id = None
#
#         if st.button("Create Employee", key="create_employee_btn"):
#             if new_emp_name and new_emp_email:
#                 if new_sys_role_id is None:
#                     st.warning("Please select a System Role.")
#                     st.stop()
#                 try:
#                     create_employee_and_add_to_system_users(new_emp_name, new_emp_email, new_emp_role, new_sys_role_id)
#                     st.success(f"✅ Employee '{new_emp_name}' created successfully!")
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"Error creating employee: {e}")
#             else:
#                 st.warning("Please enter employee name and email.")
#
#     st.write("---")
#
#     try:
#         employees = get_organisation_employees()
#
#         if employees:
#             st.write(f"**Total Employees:** {len(employees)}")
#
#             for emp_id, emp_name, emp_email, emp_role in employees:
#                 with st.expander(f"👤 {emp_name}", expanded=False):
#                     st.write(f"**Email:** {emp_email}")
#                     st.write(f"**Role:** {emp_role or 'Not specified'}")
#
#                     employee_groups = get_employees_group_memberships(emp_id)
#
#                     st.write("---")
#                     st.write(f"**Group Memberships ({len(employee_groups)}):**")
#
#                     if employee_groups:
#                         for grp_id, grp_name in employee_groups:
#                             col1, col2 = st.columns([4, 1])
#                             with col1:
#                                 st.write(f"• {grp_name}")
#                             with col2:
#                                 if st.button("Remove", key=f"emp_remove_{emp_id}_{grp_id}"):
#                                     try:
#                                         remove_employee_from_employee_groups(emp_id, grp_id)
#                                         st.success(f"✅ Removed {emp_name} from {grp_name}!")
#                                         st.rerun()
#                                     except Exception as e:
#                                         st.error(f"Error removing from group: {e}")
#                     else:
#                         st.info("Not a member of any group yet.")
#
#                     st.write("---")
#                     st.write("**Add to Group:**")
#
#                     available_groups = find_organisation_groups_employee_not_in(emp_id)
#
#                     if available_groups:
#                         group_options = {name: grp_id for grp_id, name in available_groups}
#                         selected_group = st.selectbox(
#                             "Select Group",
#                             options=list(group_options.keys()),
#                             key=f"add_group_{emp_id}"
#                         )
#
#                         if st.button("Add to Group", key=f"add_group_btn_{emp_id}"):
#                             try:
#                                 group_id = group_options[selected_group]
#                                 add_employee_to_employee_group(emp_id, group_id)
#                                 st.success(f"✅ Added {emp_name} to {selected_group}!")
#                                 st.rerun()
#                             except Exception as e:
#                                 st.error(f"Error adding to group: {e}")
#                     else:
#                         st.info("Already a member of all available groups.")
#         else:
#             st.info("No employees found in the database.")
#
#     except Exception as e:
#         st.error(f"Error loading employees: {e}")
