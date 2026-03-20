import streamlit as st

from database.init_db import init_db

if "role" not in st.session_state:
    st.session_state.role = None

try:
    init_db()
except Exception as e:
    st.error(f"Database init_databases() failed: {e}")
    import traceback
    st.error(traceback.format_exc())

def login():

    st.header("Log in")
    
    from database.system_users import validate_system_user
    
    st.info("Please use your credentials to sign in")
    username_input = st.text_input("Username or E-mail", placeholder="example@gmail.com")

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

employee_3 = st.Page(
    "employee/forms.py",
    title="Forms",
    icon=":material/assignment:",
    default=True,
)
admin_1 = st.Page(
    "admin/user_management.py",
    title="User Management",
    icon=":material/person_add:"
)

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

hr_dashboard_page = st.Page(
    "ui/pages/results/result_page.py",
    title="Dashboard",
    icon=":material/bar_chart:"
)

hr_dashboard_page2 = st.Page(
    "ui/pages/results/result2_page.py",
    title="Dashboard",
    icon=":material/bar_chart:"
)

hr_campaign_results = st.Page(
    "ui/pages/results/campaign_results_page.py",
    title="Campaign Results",
    icon=":material/assessment:"
)

account_pages = [logout_page, settings, manage_groups]
welcome_pages = [employee_3]
admin_pages = [admin_1]
hr_pages = [hr_campaigns, hr_survey_builder]
org_pages = [hr_org_page]
dashboard_pages = [hr_dashboard_page, hr_dashboard_page2, hr_campaign_results]

st.markdown("""
<style>
header.stAppHeader {
    background-color: transparent;
}
section.stMain .block-container {
    padding-top: 0rem;
    z-index: 1;
}
</style>""", unsafe_allow_html=True)

st.title("TÉR Project")

page_dict = {}
if st.session_state.role in ["Employee", "Admin", "Team Leader", "Management", "HR employee"]:
    page_dict["General"] = welcome_pages
if st.session_state.role == "Admin":
    page_dict["Organisation"] = org_pages
    page_dict["Admin"] = admin_pages
    page_dict["Dashboard"] = dashboard_pages
if st.session_state.role == "HR employee":
    page_dict["Organisation"] = org_pages
    page_dict["HR"] = hr_pages
    page_dict["Dashboard"] = dashboard_pages

if len(page_dict) > 0:
    pg = st.navigation({"Account": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login)])

pg.run()
