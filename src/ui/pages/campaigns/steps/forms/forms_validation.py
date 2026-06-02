import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.stepper.stepper_state import set_step_progress
from ui.pages.campaigns.steps.forms.forms_styles import assignment_status_html


def count_selected_pairs(role_form_map: dict) -> int:
    return sum(1 for _, form_id in role_form_map.items() if form_id)


def get_missing_pairs(role_form_map: dict) -> list[str]:
    return [
        f"{evaluator_role} → {evaluatee_role}"
        for (evaluator_role, evaluatee_role), form_id in role_form_map.items()
        if not form_id
    ]


def render_assignment_status(status_placeholder, selected_pairs: int, total_pairs: int) -> None:
    status_placeholder.markdown(
        assignment_status_html(selected_pairs == total_pairs and total_pairs > 0, selected_pairs, total_pairs),
        unsafe_allow_html=True,
    )


def save_role_form_defaults(svc: CampaignService, selected_id, campaign_id: int, role_form_map: dict) -> None:
    missing_pairs = get_missing_pairs(role_form_map)
    if missing_pairs:
        st.error(
            f"{ICONS['error']} Please select a form for every role pair before saving. "
            f"Missing: {', '.join(missing_pairs[:8])}"
            + (" ..." if len(missing_pairs) > 8 else "")
        )
        return

    svc.upsert_role_form_defaults(campaign_id, role_form_map)
    set_step_progress(selected_id, completed_phase=2, current_phase=3)
    st.success(f"{ICONS['check']} Role-form defaults saved.")
    st.rerun()
