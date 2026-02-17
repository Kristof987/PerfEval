import streamlit as st

from consts.consts import ROLES

st.title("Settings")

name = st.text_input("Name", value=st.session_state.name)
role = st.selectbox("Choose your role", ROLES, index=ROLES.index(st.session_state.role))
email = st.text_input("Email", value=st.session_state.email)