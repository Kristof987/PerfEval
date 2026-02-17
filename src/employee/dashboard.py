import streamlit as st

st.header("Dashboard")
st.write(f"You are logged in as {st.session_state.role}.")