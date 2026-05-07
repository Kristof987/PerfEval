from datetime import datetime

import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.common.common import set_step_progress
from ui.pages.campaigns.helpers.helpers import date_to_datetime


def render_setup(phase_index: int, selected_id, selected_campaign):
    if phase_index == 0:
        st.info(
            "Set up the campaign basics here (name, description, dates). "
            "This is the first step before Groups, Forms, and Matrix configuration."
        )
        if selected_id == "new":
            st.subheader("Create Campaign")
            st.info(
                "Set the basic campaign details here (name, description, dates). "
                "After saving, you can continue with Groups and Forms."
            )
            with st.form("stepper_create_campaign_form"):
                name = st.text_input("Campaign Name*", placeholder="e.g., Q1 2024 Performance Review")
                description = st.text_area("Description*", placeholder="Enter campaign description")

                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date*", value=datetime.now())
                with col2:
                    end_date = st.date_input("End Date", value=None)

                comment = st.text_area(
                    "Additional Comments (optional)",
                    placeholder="Any additional notes about this campaign",
                )

                submitted = st.form_submit_button("Create Campaign", type="primary", use_container_width=True)

                if submitted:
                    if not name or not description:
                        st.error(f"{ICONS['error']} Please fill in all required fields (marked with *)")
                    else:
                        start_datetime = date_to_datetime(start_date)
                        end_datetime = date_to_datetime(end_date)

                        try:
                            svc = CampaignService()
                            campaign_id = svc.create_campaign(
                                name=name,
                                description=description,
                                start_date=start_datetime,
                                end_date=end_datetime,
                                comment=comment if comment else None,
                            )

                            st.session_state.campaign_dashboard_selected_id = int(campaign_id)
                            set_step_progress(campaign_id, completed_phase=0, current_phase=1)
                            st.success(f"{ICONS['check']} Campaign '{name}' created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"{ICONS['error']} Failed to create campaign. {e}")
        else:
            st.subheader("Edit Campaign")
            st.info(
                "Update the campaign basics here. Changes affect the flow configuration steps that follow."
            )

            campaign = selected_campaign
            if not campaign:
                st.error("Campaign data is not available.")
                return

            current_name = getattr(campaign, "name", "")
            current_description = getattr(campaign, "description", "") or ""
            start_val = getattr(campaign, "start_date", None)
            current_start = start_val.date() if hasattr(start_val, "date") else start_val
            end_val = getattr(campaign, "end_date", None)
            current_end = end_val.date() if end_val and hasattr(end_val, "date") else end_val
            current_comment = getattr(campaign, "comment", "") or ""
            current_is_active = bool(getattr(campaign, "is_active", True))

            with st.form(f"stepper_edit_campaign_form_{selected_id}"):
                name = st.text_input("Campaign Name*", value=current_name)
                description = st.text_area("Description*", value=current_description)

                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date*", value=current_start)
                with col2:
                    end_date = st.date_input("End Date", value=current_end)

                comment = st.text_area("Additional Comments (optional)", value=current_comment)

                submitted = st.form_submit_button("Save campaign changes", type="primary", use_container_width=True)

                if submitted:
                    if not name or not description:
                        st.error(f"{ICONS['error']} Please fill in all required fields (marked with *)")
                    else:
                        start_datetime = date_to_datetime(start_date)
                        end_datetime = date_to_datetime(end_date)

                        try:
                            svc = CampaignService()
                            svc.update_campaign(
                                campaign_id=int(selected_id),
                                name=name,
                                description=description,
                                start_date=start_datetime,
                                end_date=end_datetime,
                                is_active=current_is_active,
                                comment=comment if comment else None,
                            )
                            set_step_progress(selected_id, completed_phase=0)
                            st.success(f"{ICONS['check']} Campaign '{name}' updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"{ICONS['error']} Failed to update campaign. {e}")
