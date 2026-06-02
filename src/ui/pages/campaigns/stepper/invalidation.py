import streamlit as st

from ui.pages.campaigns.stepper.session_keys import (
    CAMPAIGN_TEAMS_INVALIDATED_BY_ID_KEY,
    legacy_role_form_map_key,
    legacy_role_form_prefix,
    role_form_map_key,
    role_form_prefix,
)
from ui.pages.campaigns.stepper.stepper_state import set_step_progress


def invalidate_after_team_change(campaign_id) -> None:
    if campaign_id == "new" or campaign_id is None:
        return

    phase_key = str(campaign_id)
    invalidated_by_id = st.session_state.get(CAMPAIGN_TEAMS_INVALIDATED_BY_ID_KEY, {})
    invalidated_by_id[phase_key] = True
    st.session_state[CAMPAIGN_TEAMS_INVALIDATED_BY_ID_KEY] = invalidated_by_id

    set_step_progress(campaign_id, completed_phase=1, current_phase=1, force_completed=True, scroll_to_top=False)
    _clear_role_form_cache(phase_key)


def _clear_role_form_cache(phase_key: str) -> None:
    keys_to_delete = []
    current_map_key = role_form_map_key(phase_key)
    old_map_key = legacy_role_form_map_key(phase_key)
    current_form_prefix = role_form_prefix(phase_key)
    old_form_prefix = legacy_role_form_prefix(phase_key)

    for key in list(st.session_state.keys()):
        if key in (current_map_key, old_map_key):
            keys_to_delete.append(key)
        elif key.startswith(current_form_prefix):
            keys_to_delete.append(key)
        elif key.startswith(old_form_prefix):
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del st.session_state[key]
