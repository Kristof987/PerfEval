import streamlit as st

st.header("Profile")
st.write(f"You are logged in as {st.session_state.role}.")