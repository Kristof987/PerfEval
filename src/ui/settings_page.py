import streamlit as st
from database.connection import get_connection
from consts.consts import ROLES

st.title("Settings")

if st.session_state.role == "Admin":
    tab1, = st.tabs(["Personal Information"])
    
    with tab1:
        st.subheader("Personal Information")
        name = st.text_input("Name", value=st.session_state.name, key="personal_name")
        role = st.selectbox("Choose your role", ROLES, index=ROLES.index(st.session_state.role), key="personal_role")
        email = st.text_input("Email", value=st.session_state.email, key="personal_email")


else:
    name = st.text_input("Name", value=st.session_state.name)
    role = st.selectbox("Choose your role", ROLES, index=ROLES.index(st.session_state.role))
    email = st.text_input("Email", value=st.session_state.email)


if st.button("Save changes", type="primary"):
    st.session_state.name = name
    st.session_state.role = role
    st.session_state.email = email
    st.success("✅ Settings updated successfully.")
