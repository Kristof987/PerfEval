import runpy

import streamlit as st

from ui.pages.campaigns.common.common import set_step_progress


def render_results(selected_id, campaign_name):
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
    current_campaign_id = int(selected_id)
    embedded_campaign_key = "cr_embedded_campaign_id"
    last_embedded_campaign_id = st.session_state.get(embedded_campaign_key)

    # Keep internal Campaign Results navigation (campaign/overall/employee)
    # across reruns while staying on this stepper page. Reset only when
    # the selected campaign changes.
    if last_embedded_campaign_id != current_campaign_id:
        st.session_state.cr_view = "campaign"
        st.session_state.cr_selected_employee_id = None
        st.session_state.cr_selected_employee_name = None

    st.session_state[embedded_campaign_key] = current_campaign_id
    st.session_state.cr_selected_campaign_id = current_campaign_id
    st.session_state.cr_selected_campaign_name = campaign_name

    # Render full Campaign Results page content inline (no page navigation).
    runpy.run_path("src/ui/pages/results/campaign_results_page.py", run_name="__main__")