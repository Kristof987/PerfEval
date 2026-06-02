import runpy

import streamlit as st

from ui.pages.campaigns.stepper.stepper_state import set_step_progress


EMBEDDED_CAMPAIGN_KEY = "cr_embedded_campaign_id"


def reset_embedded_results_navigation_if_campaign_changed(campaign_id: int) -> None:
    if st.session_state.get(EMBEDDED_CAMPAIGN_KEY) == campaign_id:
        return

    st.session_state.cr_view = "campaign"
    st.session_state.cr_selected_employee_id = None
    st.session_state.cr_selected_employee_name = None


def sync_embedded_results_context(campaign_id: int, campaign_name: str) -> None:
    st.session_state[EMBEDDED_CAMPAIGN_KEY] = campaign_id
    st.session_state.cr_selected_campaign_id = campaign_id
    st.session_state.cr_selected_campaign_name = campaign_name


def render_embedded_results_page() -> None:
    runpy.run_path("src/ui/pages/results/campaign_results_page.py", run_name="__main__")


def render_results(selected_id, campaign_name) -> None:
    if selected_id == "new":
        st.warning("Create the campaign first, then open results.")
        return

    st.info(
        "Review campaign results here. Use the embedded results view to inspect participants, "
        "completion, and aggregated outcomes before final closure."
    )

    # Keep Results marked completed, but do not hard-force current_phase to 5,
    # so the top stepper remains freely clickable to earlier steps.
    set_step_progress(selected_id, completed_phase=5)

    campaign_id = int(selected_id)
    reset_embedded_results_navigation_if_campaign_changed(campaign_id)
    sync_embedded_results_context(campaign_id, campaign_name)
    render_embedded_results_page()
