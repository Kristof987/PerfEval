import streamlit as st

from database.init_tables import init_databases
from consts.consts import ROLES

if "role" not in st.session_state:
    st.session_state.role = None

try:
    init_databases()
except Exception as e:
    st.error(f"Database init_databases() failed: {e}")
    import traceback
    st.error(traceback.format_exc())

def login():

    st.header("Log in")
    
    from database.system_users import validate_system_user
    
    st.info("Please log in with your system username or name")
    username_input = st.text_input("Username or Name")

    if st.button("Log in"):
        if username_input:
            is_valid, user_data = validate_system_user(username_input)
            
            if is_valid:
                role = user_data['role_name'] if user_data['role_name'] else "Employee"
                
                st.session_state.role = role
                st.session_state.name = user_data['name']
                st.session_state.username = user_data['username']
                st.session_state.email = user_data['email']
                st.session_state.employee_id = user_data['employee_id']
                st.rerun()
            else:
                st.error("Invalid username. Please contact your administrator to create a system account.")
        else:
            st.warning("Please enter your username or name.")


def logout():
    st.session_state.role = None
    st.rerun()


role = st.session_state.role

logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
settings = st.Page("ui/settings_page.py", title="Settings", icon=":material/settings:")
manage_groups = st.Page("ui/pages/groups/my_groups_page.py", title="My Groups", icon=":material/groups:")

employee_1 = st.Page(
    "employee/dashboard.py",
    title="Dashboard",
    icon=":material/help:"
)
employee_2 = st.Page(
    "employee/profile.py", title="Profile", icon=":material/bug_report:",
    default=True,
)
employee_3 = st.Page(
    "employee/forms.py",
    title="Forms",
    icon=":material/assignment:"
)
admin_1 = st.Page(
    "admin/user_management.py",
    title="User Management",
    icon=":material/person_add:"
)
admin_2 = st.Page("admin/reports.py", title="Reports", icon=":material/security:")

hr_campaigns = st.Page(
    "ui/pages/campaigns/campaign_page.py",
    title="Campaigns",
    icon=":material/campaign:"
)

hr_survey_builder = st.Page(
    "ui/pages/forms/form_builder_page.py",
    title="Form Builder",
    icon=":material/edit_note:"
)

hr_org_page = st.Page(
    "ui/pages/organisation/org_info_page.py",
    title="Organisation Information",
    icon=":material/badge:"
)

account_pages = [logout_page, settings, manage_groups]
welcome_pages = [employee_1, employee_2, employee_3]
admin_pages = [admin_1, admin_2]
hr_pages = [hr_campaigns, hr_survey_builder]
org_pages = [hr_org_page]

st.title("TÉR Project")

page_dict = {}
if st.session_state.role in ["Employee", "Admin", "Team Leader", "Management", "HR employee"]:
    page_dict["General"] = welcome_pages
if st.session_state.role == "Admin":
    page_dict["Organisation"] = org_pages
    page_dict["Admin"] = admin_pages
if st.session_state.role == "HR employee":
    page_dict["Organisation"] = org_pages
    page_dict["HR"] = hr_pages

if len(page_dict) > 0:
    pg = st.navigation({"Account": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login)])

pg.run()
