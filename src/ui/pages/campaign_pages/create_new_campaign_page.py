from datetime import datetime

import streamlit as st

from consts.consts import ICONS
from hr.campaigns import create_campaign


class CreateNewCampaignPage:
    def __init__(self, query_params):
        self.query_params = query_params

    def create(self):
        with st.form("create_campaign_form"):
            st.subheader(f"{ICONS['add']} Create New Campaign")

            name = st.text_input("Campaign Name*", placeholder="e.g., Q1 2024 Performance Review")
            description = st.text_area("Description*", placeholder="Enter campaign description")

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date*", value=datetime.now())
            with col2:
                end_date = st.date_input("End Date", value=None)

            comment = st.text_area("Additional Comments (optional)",
                                   placeholder="Any additional notes about this campaign")

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("Create Campaign", type="primary", use_container_width=True)
            with col_cancel:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                if not name or not description:
                    st.error(f"{ICONS['error']} Please fill in all required fields (marked with *)")
                else:
                    # Convert dates to datetime
                    start_datetime = datetime.combine(start_date, datetime.min.time())
                    end_datetime = datetime.combine(end_date, datetime.min.time()) if end_date else None

                    campaign_id = create_campaign(
                        name=name,
                        description=description,
                        start_date=start_datetime,
                        end_date=end_datetime,
                        comment=comment if comment else None
                    )

                    if campaign_id:
                        st.success(f"{ICONS['check']} Campaign '{name}' created successfully!")
                        self.query_params.clear()
                        st.rerun()
                    else:
                        st.error(f"{ICONS['error']} Failed to create campaign. Campaign name might already exist.")

            if cancelled:
                self.query_params.clear()
                st.rerun()