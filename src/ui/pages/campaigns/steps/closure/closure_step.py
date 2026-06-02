import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.helpers.helpers import get
from ui.pages.campaigns.stepper.stepper_state import set_step_progress


CLOSED_MARKER = "[CLOSED]"


def is_campaign_closed(campaign) -> bool:
    return CLOSED_MARKER in str(get(campaign, "comment") or "")


def close_campaign(service: CampaignService, campaign_id: int) -> None:
    service.close_campaign(campaign_id)


def mark_closure_progress(selected_id) -> None:
    set_step_progress(selected_id, completed_phase=6, current_phase=6, force_completed=True)


def render_close_campaign_action(service: CampaignService, selected_id, campaign_id: int) -> None:
    if not st.button("Close Campaign", type="primary", key=f"stepper_close_campaign_{campaign_id}"):
        return

    try:
        close_campaign(service, campaign_id)
        mark_closure_progress(selected_id)
        st.success("Campaign closed.")
        st.rerun()
    except Exception as exc:
        st.error(f"{ICONS['error']} Could not close campaign: {exc}")


def render_closure(selected_id) -> None:
    st.subheader("Closure")
    if selected_id == "new":
        st.warning("Create the campaign first, then close it when the flow is finished.")
        return

    service = CampaignService()
    campaign_id = int(selected_id)
    campaign = service.get_campaign(campaign_id)
    if campaign is None:
        st.error("Campaign data is not available.")
        return

    st.caption("Finalize the campaign and lock it as closed.")

    if is_campaign_closed(campaign):
        mark_closure_progress(selected_id)
        st.success("Campaign is already closed.")
        return

    render_close_campaign_action(service, selected_id, campaign_id)
