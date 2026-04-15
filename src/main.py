import streamlit as st

from database.init_db import init_db
from persistence.repository.org_employees_repo import OrgEmployeesRepository
from persistence.repository.system_permissions_repo import SystemPermissionsRepository
from persistence.repository.system_roles_repo import SystemRolesRepository
from persistence.repository.system_users_repo import SystemUsersRepository
from services.system_user_service import SystemUserService


def _dedupe_pages(pages: list):
    """Keep first page per title to avoid duplicate sidebar entries."""
    seen = set()
    unique = []
    for page in pages:
        key = (getattr(page, "title", None) or str(page)).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(page)
    return unique

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

    service = SystemUserService(
        users_repo=SystemUsersRepository(),
        roles_repo=SystemRolesRepository(),
        permissions_repo=SystemPermissionsRepository(),
        employees_repo=OrgEmployeesRepository(),
    )
    
    st.info("Please use your credentials to sign in")
    username_input = st.text_input("Username or E-mail", placeholder="example@gmail.com")

    if st.button("Log in"):
        if username_input:
            login_result = service.validate_system_user(username_input)
            is_valid, user_data = login_result.is_valid, login_result.user_data
            
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
    "ui/pages/employee/forms_page.py",
    title="Assigned Forms",
    icon=":material/assignment:",
    default=True,
)
admin_1 = st.Page(
    "ui/pages/admin/user_management_page.py",
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
    title="Create & Edit Forms",
    icon=":material/edit_note:"
)

hr_org_page = st.Page(
    "ui/pages/organisation/org_info_page.py",
    title="Organisation Information",
    icon=":material/badge:"
)

# hr_dashboard_page = st.Page(
#     "ui/pages/results/result_page.py",
#     title="Analytics",
#     icon=":material/bar_chart:"
# )

# hr_dashboard_page2 = st.Page(
#     "ui/pages/results/result2_page.py",
#     title="Analytics",
#     icon=":material/bar_chart:"
# )

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
dashboard_pages = [hr_campaign_results]

account_pages = _dedupe_pages(account_pages)
welcome_pages = _dedupe_pages(welcome_pages)
admin_pages = _dedupe_pages(admin_pages)
hr_pages = _dedupe_pages(hr_pages)
org_pages = _dedupe_pages(org_pages)
dashboard_pages = _dedupe_pages(dashboard_pages)

st.markdown("""
<style>
header.stAppHeader {
    background-color: transparent;
}
section.stMain .block-container {
    padding-top: 0rem;
    z-index: 1;
}
.st-key-top_profile_icon button {
    width: 42px;
    height: 42px;
    border-radius: 999px;
    border: 1px solid #cbd5e1;
    background-image: url("https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&h=200&fit=crop");
    background-size: cover;
    background-position: center;
    color: transparent;
    padding: 0;
}
.st-key-top_profile_icon button:hover {
    border-color: #60a5fa;
    box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.25);
}
.st-key-top_profile_icon button:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25);
}
</style>""", unsafe_allow_html=True)

title_col, profile_col = st.columns([0.92, 0.08], vertical_alignment="center")

with title_col:
    st.title("PerfEval Project")

with profile_col:
    if st.session_state.role is not None:
        if st.button("profile", key="top_profile_icon", help="Settings"):
            st.switch_page("ui/settings_page.py")

page_dict = {}
if st.session_state.role in ["Employee", "Admin", "Team Leader", "Management", "HR employee"]:
    page_dict["General"] = welcome_pages
if st.session_state.role == "Admin":
    page_dict["Organisation"] = org_pages
    page_dict["Admin"] = admin_pages
    page_dict["Results"] = dashboard_pages
if st.session_state.role == "HR employee":
    page_dict["Organisation"] = org_pages
    page_dict["Admin"] = admin_pages
    page_dict["HR"] = hr_pages
    page_dict["Results"] = dashboard_pages

if len(page_dict) > 0:
    pg = st.navigation({"Account": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login)])

pg.run()
