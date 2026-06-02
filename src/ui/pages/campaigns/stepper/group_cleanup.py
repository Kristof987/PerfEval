import streamlit as st

from services.campaign_service import CampaignService
from ui.pages.campaigns.stepper.session_keys import (
    matrix_editor_prefix,
    matrix_selections_key,
    percentage_input_prefix,
    percentage_key,
)


def cleanup_on_group_removal(campaign_id: int, group_id: int) -> None:
    """
    Remove a group from a campaign and clean up matrix assignments,
    role-form defaults that no longer apply, and related session state.
    """
    svc = CampaignService()

    try:
        svc.save_evaluations_batch(campaign_id, group_id, [], {})
    except Exception:
        pass

    _clear_group_matrix_state(campaign_id, group_id)

    svc.remove_group_from_campaign(campaign_id, group_id)
    _remove_orphaned_role_form_defaults(svc, campaign_id)


def _clear_group_matrix_state(campaign_id: int, group_id: int) -> None:
    matrix_key = matrix_selections_key(campaign_id, group_id)
    st.session_state.pop(matrix_key, None)

    editor_prefix = matrix_editor_prefix(matrix_key)
    quick_percentage_key = percentage_key(campaign_id, group_id)
    quick_percentage_input_prefix = percentage_input_prefix(quick_percentage_key)
    for key in list(st.session_state.keys()):
        if key.startswith(editor_prefix):
            del st.session_state[key]
        elif key == quick_percentage_key:
            del st.session_state[key]
        elif key.startswith(quick_percentage_input_prefix):
            del st.session_state[key]


def _remove_orphaned_role_form_defaults(svc: CampaignService, campaign_id: int) -> None:
    remaining_role_names = set(svc.list_campaign_role_names(campaign_id))

    current_defaults = svc.get_role_form_defaults(campaign_id)
    if not current_defaults:
        return

    cleaned_defaults = {
        (evaluator_role, evaluatee_role): form_id
        for (evaluator_role, evaluatee_role), form_id in current_defaults.items()
        if evaluator_role in remaining_role_names and evaluatee_role in remaining_role_names
    }
    if len(cleaned_defaults) != len(current_defaults):
        svc.upsert_role_form_defaults(campaign_id, cleaned_defaults)
