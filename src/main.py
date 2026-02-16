from pathlib import Path

import streamlit as st

if "role" not in st.session_state:
    st.session_state.role = None

ROLES = [
    None,
    "Employee",
    "Team Leader",
    "HR Employee",
    "Management",
    "Admin",
]

def login():

    st.header("Log in")
    role = st.selectbox("Choose your role", ROLES, help="**Which role to choose?**\n\nTODO....")
    name = st.text_input("Username or E-mail")

    if st.button("Log in"):
        st.session_state.role = role
        st.session_state.name = name #Unused for now
        st.rerun()


def logout():
    st.session_state.role = None
    st.rerun()


role = st.session_state.role

logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
settings = st.Page("settings.py", title="Settings", icon=":material/settings:")
employee_1 = st.Page(
    "employee/employee_1.py",
    title="Employee 1",
    icon=":material/help:",
    default=(role == "Employee"),
)
employee_2 = st.Page(
    "employee/employee_2.py", title="Employee 2", icon=":material/bug_report:"
)
admin_1 = st.Page(
    "admin/admin_1.py",
    title="Admin 1",
    icon=":material/person_add:",
    default=(role == "Admin"),
)
admin_2 = st.Page("admin/admin_2.py", title="Admin 2", icon=":material/security:")

account_pages = [logout_page, settings]
request_pages = [employee_1, employee_2]
admin_pages = [admin_1, admin_2]

st.title("Request manager")

page_dict = {}
if st.session_state.role in ["Employee", "Admin", "Team Leader"]:
    page_dict["Request"] = request_pages
if st.session_state.role == "Admin":
    page_dict["Admin"] = admin_pages

if len(page_dict) > 0:
    pg = st.navigation({"Account": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login)])

pg.run()
