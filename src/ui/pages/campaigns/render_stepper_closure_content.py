import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.common.common import set_step_progress
from ui.pages.campaigns.helpers.helpers import get


def render_closure(selected_id):
    st.subheader("Closure")
    if selected_id == "new":
        st.warning("Create the campaign first, then close it when the flow is finished.")
        return

    svc = CampaignService()
    campaign_id = int(selected_id)
    campaign = svc.get_campaign(campaign_id)
    if campaign is None:
        st.error("Campaign data is not available.")
        return

    comment = str(get(campaign, "comment") or "")
    # Consider campaign closed only when the explicit CLOSED marker is present.
    # This prevents "already closed" from appearing after filling is closed
    # (which sets is_active=False with [PENDING_RESULTS]).
    is_closed = "[CLOSED]" in comment

    st.caption("Finalize the campaign and lock it as closed.")

    if is_closed:
        set_step_progress(selected_id, completed_phase=6, current_phase=6, force_completed=True)
        st.success("Campaign is already closed.")
        return

    if st.button("Close Campaign", type="primary", key=f"stepper_close_campaign_{campaign_id}"):
        try:
            close_campaign_fn = getattr(svc, "close_campaign", None)
            if callable(close_campaign_fn):
                close_campaign_fn(campaign_id)
            else:
                with svc.db.transaction() as conn:
                    svc.campaigns.close_campaign(conn, campaign_id)

            set_step_progress(selected_id, completed_phase=6, current_phase=6, force_completed=True)
            st.success("Campaign closed.")
            st.rerun()
        except Exception as exc:
            st.error(f"{ICONS['error']} Could not close campaign: {exc}")