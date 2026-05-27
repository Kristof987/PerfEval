import pandas as pd

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.common.common import set_step_progress
import streamlit as st

from ui.pages.campaigns.helpers.helpers import get

def render_evaluation(selected_id):
    st.subheader("Evaluate")
    st.caption("Collect responses and continue when ready")

    svc = CampaignService()
    campaign_id = int(selected_id)
    campaign = svc.get_campaign(campaign_id)
    evaluations = svc.list_campaign_evaluations(campaign_id)

    remaining_by_evaluator: dict[str, int] = {}
    completed_by_evaluator: dict[str, int] = {}
    assigned_by_evaluator: dict[str, int] = {}

    for row in evaluations:
        evaluator_name = str(get(row, "evaluator_name", "Unknown"))
        status = str(get(row, "status", "")).lower()

        assigned_by_evaluator[evaluator_name] = assigned_by_evaluator.get(evaluator_name, 0) + 1
        if status == "completed":
            completed_by_evaluator[evaluator_name] = completed_by_evaluator.get(evaluator_name, 0) + 1
        else:
            remaining_by_evaluator[evaluator_name] = remaining_by_evaluator.get(evaluator_name, 0) + 1

    total_remaining = sum(remaining_by_evaluator.values())
    total_assigned = sum(assigned_by_evaluator.values())
    total_completed = sum(completed_by_evaluator.values())

    m1, m2, m3 = st.columns(3)
    m1.metric("Remaining questionnaires", total_remaining)
    m2.metric("Completed questionnaires", total_completed)
    m3.metric("Assigned questionnaires", total_assigned)

    if total_remaining == 0 and total_assigned > 0:
        st.success("All questionnaires are completed.")
    elif total_assigned == 0:
        st.info("No questionnaires assigned yet.")
    else:
        st.warning(f"{total_remaining} questionnaires are still pending.")

    if assigned_by_evaluator:
        rows = []
        for evaluator_name, assigned_count in assigned_by_evaluator.items():
            completed_count = completed_by_evaluator.get(evaluator_name, 0)
            remaining_count = assigned_count - completed_count
            rows.append(
                {
                    "Employee": evaluator_name,
                    "Remaining": remaining_count,
                    "Completed": completed_count,
                    "Assigned": assigned_count,
                }
            )

        rows = sorted(rows, key=lambda r: (-r["Remaining"], r["Employee"]))
        st.write("**Remaining questionnaires by employee**")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if campaign and bool(get(campaign, "is_active", True)):
        if st.button("Close Form Filling", type="primary", key="stepper_close_filling"):
            try:
                close_fn = getattr(svc, "close_filling_period", None)
                if callable(close_fn):
                    close_fn(campaign_id)
                else:
                    # Backward-compatible fallback if old service instance is loaded
                    with svc.db.transaction() as conn:
                        svc.campaigns.close_filling_period(conn, campaign_id)
                set_step_progress(selected_id, completed_phase=4, current_phase=5)
                st.success("Filling period closed.")
                st.rerun()
            except Exception as exc:
                st.error(f"{ICONS['error']} Could not close filling period: {exc}")
    else:
        set_step_progress(selected_id, current_phase=5)
        st.rerun()