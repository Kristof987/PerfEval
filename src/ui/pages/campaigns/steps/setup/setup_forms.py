from datetime import datetime

import streamlit as st

from ui.pages.campaigns.steps.setup.setup_actions import create_campaign_from_form, update_campaign_from_form


def render_create_campaign_form() -> None:
    st.info(
        "Set the basic campaign details here (name, description, dates). "
        "After saving, you can continue with Groups and Forms."
    )
    with st.form("stepper_create_campaign_form"):
        form_values = _render_campaign_fields(
            name="",
            description="",
            start_date=datetime.now(),
            end_date=None,
            comment="",
        )

        submitted = st.form_submit_button("Create Campaign", type="primary", use_container_width=True)
        if submitted:
            create_campaign_from_form(**form_values)


def render_edit_campaign_form(selected_id, selected_campaign) -> None:
    if not selected_campaign:
        st.error("Campaign data is not available.")
        return

    form_values = _campaign_form_defaults(selected_campaign)
    current_is_active = bool(getattr(selected_campaign, "is_active", True))

    with st.form(f"stepper_edit_campaign_form_{selected_id}"):
        submitted_values = _render_campaign_fields(**form_values)

        submitted = st.form_submit_button("Save campaign changes", type="primary", use_container_width=True)
        if submitted:
            update_campaign_from_form(
                campaign_id=int(selected_id),
                is_active=current_is_active,
                **submitted_values,
            )


def _render_campaign_fields(name: str, description: str, start_date, end_date, comment: str) -> dict:
    name = st.text_input("Campaign Name*", value=name, placeholder="e.g., Q1 2024 Performance Review")
    description = st.text_area("Description*", value=description, placeholder="Enter campaign description")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date*", value=start_date)
    with col2:
        end_date = st.date_input("End Date", value=end_date)

    comment = st.text_area(
        "Additional Comments (optional)",
        value=comment,
        placeholder="Any additional notes about this campaign",
    )

    return {
        "name": name,
        "description": description,
        "start_date": start_date,
        "end_date": end_date,
        "comment": comment,
    }


def _campaign_form_defaults(campaign) -> dict:
    start_val = getattr(campaign, "start_date", None)
    end_val = getattr(campaign, "end_date", None)
    return {
        "name": getattr(campaign, "name", ""),
        "description": getattr(campaign, "description", "") or "",
        "start_date": start_val.date() if hasattr(start_val, "date") else start_val,
        "end_date": end_val.date() if end_val and hasattr(end_val, "date") else end_val,
        "comment": getattr(campaign, "comment", "") or "",
    }
