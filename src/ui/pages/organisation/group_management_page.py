import runpy
import streamlit as st

st.session_state.org_info_mode = "groups"
runpy.run_path("src/ui/pages/organisation/org_info_page.py", run_name="__main__")

