import streamlit as st

from ui.pages.campaigns.steps.setup.setup_forms import render_create_campaign_form, render_edit_campaign_form


def render_setup(phase_index: int, selected_id, selected_campaign) -> None:
    if phase_index != 0:
        return

    if selected_id == "new":
        st.info(
            "Set up the campaign basics here (name, description, dates). "
            "This is the first step before Groups, Forms, and Matrix configuration."
        )
        st.subheader("Create Campaign")
        render_create_campaign_form()
        return

    st.subheader("Edit Campaign")
    st.info("Update the campaign basics here. Changes affect the flow configuration steps that follow.")
    render_edit_campaign_form(selected_id, selected_campaign)
