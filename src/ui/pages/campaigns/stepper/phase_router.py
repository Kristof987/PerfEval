import streamlit as st
import streamlit.components.v1 as components

from ui.pages.campaigns.common.consts import PHASES
from ui.pages.campaigns.steps.closure.closure_step import render_closure
from ui.pages.campaigns.steps.evaluate.evaluate_step import render_evaluation
from ui.pages.campaigns.steps.results.results_step import render_results
from ui.pages.campaigns.steps.setup.setup_step import render_setup
from ui.pages.campaigns.steps.forms.forms_step import render_forms
from ui.pages.campaigns.steps.groups.groups_step import render_groups
from ui.pages.campaigns.steps.reviewers.reviewers_step import render_reviewers
from ui.pages.campaigns.stepper.session_keys import STEPPER_SCROLL_TO_TOP_KEY
from ui.pages.campaigns.stepper.stepper_styles import PHASE_CONTENT_DIVIDER_HTML, SCROLL_TO_TOP_SCRIPT


def render_scroll_to_top_if_requested() -> None:
    if st.session_state.pop(STEPPER_SCROLL_TO_TOP_KEY, False):
        components.html(SCROLL_TO_TOP_SCRIPT, height=0)


def render_phase_content(phase_index: int, selected_id, campaign_name: str, selected_campaign) -> None:
    render_scroll_to_top_if_requested()
    st.markdown(PHASE_CONTENT_DIVIDER_HTML, unsafe_allow_html=True)

    phase_renderers = {
        0: lambda: render_setup(phase_index, selected_id, selected_campaign),
        1: lambda: render_groups(selected_id),
        2: lambda: render_forms(selected_id),
        3: lambda: render_reviewers(selected_id),
        4: lambda: render_evaluation(selected_id),
        5: lambda: render_results(selected_id, campaign_name),
        6: lambda: render_closure(selected_id),
    }
    phase_renderers.get(phase_index, lambda: render_closure(selected_id))()
