"""
This page has been superseded by the inline employee result view
embedded inside campaign_results_page.py.

It is no longer registered in the sidebar navigation.
Navigate to an employee's result from Campaign Results instead.
"""
import streamlit as st

if st.button("Go to Campaign Results"):
    st.switch_page("ui/pages/results/campaign_results_page.py")
