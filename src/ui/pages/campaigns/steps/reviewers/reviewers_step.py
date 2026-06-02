import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.steps.reviewers.reviewers_matrix import read_matrix_dataframe_selection, render_matrix_editor
from ui.pages.campaigns.steps.reviewers.reviewers_quick_actions import render_quick_actions
from ui.pages.campaigns.steps.reviewers.reviewers_save import render_matrix_save_actions
from ui.pages.campaigns.steps.reviewers.reviewers_state import (
    build_group_options,
    init_matrix_selection_state,
    matrix_key_for,
)
from ui.pages.campaigns.steps.reviewers.reviewers_styles import render_matrix_status


def load_reviewers_context(svc: CampaignService, campaign_id: int, selected_group_id: int) -> tuple[list, dict, list, list]:
    members = svc.list_group_members(selected_group_id)
    evaluation_matrix = svc.get_campaign_group_evaluations(campaign_id, selected_group_id)
    forms = svc.list_forms()
    role_names = svc.list_campaign_role_names(campaign_id)
    return members, evaluation_matrix, forms, role_names


def render_reviewers(selected_id) -> None:
    st.subheader("Evaluation matrix")
    status_placeholder = st.empty()

    if selected_id == "new":
        st.warning("Create the campaign first, then configure the matrix.")
        return

    svc = CampaignService()
    campaign_id = int(selected_id)
    assigned_groups = svc.list_campaign_groups(campaign_id)
    if not assigned_groups:
        st.warning("No assigned groups found. Assign a team first.")
        return

    group_options = build_group_options(assigned_groups)
    if not group_options:
        st.warning("No valid team found for matrix configuration.")
        return

    selected_group_name = st.selectbox("Team", options=list(group_options.keys()), key=f"stepper_matrix_group_{selected_id}")
    selected_group_id = int(group_options[selected_group_name])
    members, evaluation_matrix, forms, role_names = load_reviewers_context(svc, campaign_id, selected_group_id)
    matrix_key = matrix_key_for(campaign_id, selected_group_id)
    init_matrix_selection_state(matrix_key, evaluation_matrix)

    if not members:
        st.info("No members found in this team.")
        return

    st.info(
        "Rows represent employees being evaluated, columns represent evaluators.\n"
        "Select a cell to assign an evaluation relationship."
    )

    if not forms:
        st.error(f"{ICONS['error']} No forms available. Please create an evaluation form first.")
        return

    if not role_names:
        st.error(
            f"{ICONS['error']} No campaign roles available. "
            "Assign groups and roles before creating evaluations."
        )
        return

    edited_df = render_matrix_editor(matrix_key, members, st.session_state[matrix_key])
    st.session_state[matrix_key] = read_matrix_dataframe_selection(edited_df, members)
    render_matrix_status(status_placeholder, len(st.session_state[matrix_key]))
    render_quick_actions(campaign_id, selected_group_id, matrix_key, members)
    render_matrix_save_actions(svc, selected_id, campaign_id, selected_group_id, matrix_key)
