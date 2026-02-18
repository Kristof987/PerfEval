import streamlit as st

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
        st.info("📋 This section is for organization-wide settings and configurations.")
        st.write("")
        st.write("**Coming Soon:**")
        st.write("- Organization name and details")
        st.write("- Default evaluation templates")
        st.write("- System-wide preferences")
        st.write("- Integration settings")

else:
    # For non-Admin users, show only personal information
    name = st.text_input("Name", value=st.session_state.name)
    role = st.selectbox("Choose your role", ROLES, index=ROLES.index(st.session_state.role))
    email = st.text_input("Email", value=st.session_state.email)
