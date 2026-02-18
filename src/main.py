import streamlit as st

from database.init_tables import init_databases
from consts.consts import ROLES
from database.login import init_db
from services.auth import login_user

if "role" not in st.session_state:
    st.session_state.role = None

# Initialize database on app start
try:
    init_db()
    init_databases()
except Exception as e:
    st.error(f"Database connection failed: {e}")

def login():

    st.header("Log in")
    role = st.selectbox("Choose your role", ROLES, help="**Which role to choose?**\n\nTODO....")
    name = st.text_input("Username or E-mail")
    email = st.text_input("Email")

    if st.button("Log in"):
        if name and role:
            login_user(name, role, email)
            st.session_state.role = role
            st.session_state.name = name
            st.session_state.email = email
            st.rerun()
        else:
            st.warning("Please enter a username and select a role.")


def logout():
    st.session_state.role = None
    st.rerun()


role = st.session_state.role

logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
settings = st.Page("ui/settings_page.py", title="Settings", icon=":material/settings:")
manage_teams = st.Page("ui/manage_teams.py", title="My Teams", icon=":material/groups:")

employee_1 = st.Page(
    "employee/dashboard.py",
    title="Dashboard",
    icon=":material/help:"
)
employee_2 = st.Page(
    "employee/profile.py", title="Profile", icon=":material/bug_report:",
    default=True,
)
admin_1 = st.Page(
    "admin/user_management.py",
    title="User Management",
    icon=":material/person_add:"
)
admin_2 = st.Page("admin/reports.py", title="Reports", icon=":material/security:")

hr_campaigns = st.Page(
    "ui/campaign_page.py",
    title="Campaigns",
    icon=":material/campaign:"
)

account_pages = [logout_page, settings, manage_teams]
welcome_pages = [employee_1, employee_2]
admin_pages = [admin_1, admin_2]
hr_pages = [hr_campaigns]

st.title("TÉR Project")

page_dict = {}
if st.session_state.role in ["Employee", "Admin", "Team Leader", "Management", "HR employee"]:
    page_dict["Welcome"] = welcome_pages
if st.session_state.role == "Admin":
    page_dict["Admin"] = admin_pages
if st.session_state.role == "HR employee":
    page_dict["HR"] = hr_pages

if len(page_dict) > 0:
    pg = st.navigation({"Account": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login)])

pg.run()
