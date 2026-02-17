import streamlit as st

st.header("User Management")
st.write(f"You are logged in as {st.session_state.role}.")