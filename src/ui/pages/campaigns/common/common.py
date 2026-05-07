import streamlit as st

from services.campaign_service import CampaignService


#TODO: remove from here
def set_step_progress(
    campaign_id,
    completed_phase: int | None = None,
    current_phase: int | None = None,
    force_completed: bool = False,
    scroll_to_top: bool = True,
) -> None:
    if campaign_id == "new" or campaign_id is None:
        return

    phase_key = str(campaign_id)

    completed_by_id = st.session_state.get("campaign_dashboard_completed_phase_by_id", {})
    previous_completed = int(completed_by_id.get(phase_key, -1))
    if completed_phase is not None:
        if force_completed:
            completed_by_id[phase_key] = int(completed_phase)
        else:
            completed_by_id[phase_key] = max(previous_completed, int(completed_phase))
    st.session_state.campaign_dashboard_completed_phase_by_id = completed_by_id

    if completed_phase is not None and int(completed_phase) >= 2:
        invalidated_by_id = st.session_state.get("campaign_dashboard_teams_invalidated_by_id", {})
        invalidated_by_id[phase_key] = False
        st.session_state.campaign_dashboard_teams_invalidated_by_id = invalidated_by_id

    if current_phase is not None:
        phase_by_id = st.session_state.get("campaign_dashboard_phase_by_id", {})
        phase_by_id[phase_key] = int(current_phase)
        st.session_state.campaign_dashboard_phase_by_id = phase_by_id

        # Force pills widget recreation on next run to avoid stale selection
        nonce_by_id = st.session_state.get("campaign_stepper_widget_nonce_by_id", {})
        nonce_by_id[phase_key] = int(nonce_by_id.get(phase_key, 0)) + 1
        st.session_state.campaign_stepper_widget_nonce_by_id = nonce_by_id
        # Clear the pills widget cache so it picks up the new default
        pills_key = f"stepper_pills_{phase_key}"
        if pills_key in st.session_state:
            del st.session_state[pills_key]
        # Signal scroll-to-top after rerun (optional)
        if scroll_to_top:
            st.session_state["_stepper_scroll_to_top"] = True

#TODO: remove from here
def cleanup_on_group_removal(campaign_id: int, group_id: int) -> None:
    """
    When a group is removed from a campaign:
    1. Clear all evaluation matrix assignments for this group
    2. Remove the group from the campaign
    3. Remove role-form defaults for roles that no longer exist in remaining groups
    4. Clean up related session state
    """
    svc = CampaignService()

    # 1. Clear matrix assignments for this group
    try:
        svc.save_evaluations_batch(campaign_id, group_id, [], {})
    except Exception:
        pass

    # 2. Clean up session state for this group's matrix
    matrix_key = f"stepper_matrix_selections_{campaign_id}_{group_id}"
    if matrix_key in st.session_state:
        del st.session_state[matrix_key]
    # Also clean up related editor/percentage keys
    for key in list(st.session_state.keys()):
        if key.startswith(f"stepper_matrix_editor_{matrix_key}"):
            del st.session_state[key]
        elif key == f"stepper_percentage_{campaign_id}_{group_id}":
            del st.session_state[key]
        elif key.startswith(f"stepper_percentage_input_stepper_percentage_{campaign_id}_{group_id}"):
            del st.session_state[key]

    # 3. Remove the group from campaign
    svc.remove_group_from_campaign(campaign_id, group_id)

    # 4. Get remaining roles after removal and clean up orphaned role-form defaults
    remaining_role_names = set(svc.list_campaign_role_names(campaign_id))

    current_defaults = svc.get_role_form_defaults(campaign_id)
    if current_defaults:
        cleaned_defaults = {
            (evaluator_role, evaluatee_role): form_id
            for (evaluator_role, evaluatee_role), form_id in current_defaults.items()
            if evaluator_role in remaining_role_names and evaluatee_role in remaining_role_names
        }
        # Only update if something was actually removed
        if len(cleaned_defaults) != len(current_defaults):
            svc.upsert_role_form_defaults(campaign_id, cleaned_defaults)

#TODO: remove from here
def invalidate_after_team_change(campaign_id) -> None:
    if campaign_id == "new" or campaign_id is None:
        return

    phase_key = str(campaign_id)
    invalidated_by_id = st.session_state.get("campaign_dashboard_teams_invalidated_by_id", {})
    invalidated_by_id[phase_key] = True
    st.session_state.campaign_dashboard_teams_invalidated_by_id = invalidated_by_id

    set_step_progress(campaign_id, completed_phase=1, current_phase=1, force_completed=True, scroll_to_top=False)

    # Clear role-form related UI/session caches so removed-group effects are visible immediately.
    keys_to_delete = []
    for key in list(st.session_state.keys()):
        if key == f"stepper_role_form_map_{phase_key}":
            keys_to_delete.append(key)
        elif key == f"role_form_map_{phase_key}":
            keys_to_delete.append(key)
        elif key.startswith(f"stepper_role_form_{phase_key}_"):
            keys_to_delete.append(key)
        elif key.startswith(f"role_form_{phase_key}_"):
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del st.session_state[key]