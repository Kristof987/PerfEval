import streamlit as st
from persistence.db.connection import get_db
from persistence.repository.campaign_repo import CampaignRepository
from services.campaign_results_service import CampaignResultsService
from ui.pages.results.campaign_results_campaign_view import render_campaign_view
from ui.pages.results.campaign_results_employee_view import go_back_to_campaign_results, render_employee_view
from ui.pages.results.charts import render_summary_dashboard


campaign_repo = CampaignRepository()
campaign_results_service = CampaignResultsService()
db = get_db()

# -------------------------
# Session State Init
# -------------------------
if "cr_view" not in st.session_state:
    st.session_state.cr_view = "campaign"  # "campaign" or "employee" or "overall"
if "cr_selected_campaign_id" not in st.session_state:
    st.session_state.cr_selected_campaign_id = None
if "cr_selected_campaign_name" not in st.session_state:
    st.session_state.cr_selected_campaign_name = None
if "cr_selected_employee_id" not in st.session_state:
    st.session_state.cr_selected_employee_id = None
if "cr_selected_employee_name" not in st.session_state:
    st.session_state.cr_selected_employee_name = None

def render_overall_view():
    st.title("Campaign Overall Results")
    st.caption(f"Campaign: {st.session_state.cr_selected_campaign_name}")
    st.divider()
    campaign_id = st.session_state.cr_selected_campaign_id
    evaluations = campaign_results_service.get_evaluations_for_campaign(campaign_id)
    render_summary_dashboard(evaluations, key_prefix="overall")
    st.divider()
    if st.button("← Back to Campaign Results", key="btn_back_campaign_results_overall"):
        go_back_to_campaign_results()

def render_page():
    if st.session_state.cr_view == "overall":
        render_overall_view()
    elif st.session_state.cr_view == "employee":
        render_employee_view(db, campaign_results_service)
    else:
        render_campaign_view(db, campaign_repo, campaign_results_service)


render_page()
