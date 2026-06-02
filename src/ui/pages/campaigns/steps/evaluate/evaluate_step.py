import streamlit as st

from services.campaign_service import CampaignService
from ui.pages.campaigns.helpers.helpers import get
from ui.pages.campaigns.steps.evaluate.evaluate_actions import advance_to_results_if_needed, render_close_filling_action
from ui.pages.campaigns.steps.evaluate.evaluate_summary import (
    build_evaluation_summary,
    render_evaluation_metrics,
    render_remaining_by_employee_table,
)


def render_evaluation(selected_id) -> None:
    st.subheader("Evaluate")
    st.caption("Collect responses and continue when ready")

    svc = CampaignService()
    campaign_id = int(selected_id)
    campaign = svc.get_campaign(campaign_id)
    summary = build_evaluation_summary(svc.list_campaign_evaluations(campaign_id))

    render_evaluation_metrics(summary)
    render_remaining_by_employee_table(summary)

    if campaign and bool(get(campaign, "is_active", True)):
        render_close_filling_action(svc, selected_id, campaign_id)
        return

    if advance_to_results_if_needed(selected_id):
        st.rerun()

    st.info("Filling period is already closed. Continue to the results step.")
