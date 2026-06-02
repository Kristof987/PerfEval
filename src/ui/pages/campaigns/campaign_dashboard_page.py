from __future__ import annotations

import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.dashboard.dashboard_state import init_dashboard_state
from ui.pages.campaigns.dashboard.dashboard_styles import DASHBOARD_COMPACT_CSS
from ui.pages.campaigns.dashboard.dashboard_view import (
    build_campaign_dashboard_rows,
    load_all_campaign_counts,
    load_campaigns_or_stop,
    render_campaign_sections,
    render_create_campaign_button,
)


def render_campaign_dashboard_page() -> None:
    st.set_page_config(layout="wide")
    st.markdown(DASHBOARD_COMPACT_CSS, unsafe_allow_html=True)
    st.markdown("### Evaluation Campaigns")
    st.caption("Manage performance evaluation cycles")

    service = CampaignService()
    campaigns = load_campaigns_or_stop(service)
    if not campaigns:
        st.info(f"{ICONS.get('info', ':material/info:')} No campaigns found.")
        st.stop()

    init_dashboard_state()
    all_counts = load_all_campaign_counts(service)
    rows = build_campaign_dashboard_rows(campaigns, all_counts)
    render_campaign_sections(service, rows, all_counts)
    render_create_campaign_button()


render_campaign_dashboard_page()
