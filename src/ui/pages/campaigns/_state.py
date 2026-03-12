import streamlit as st

def init_state():
    defaults = {
        "show_edit_dialog": False,
        "edit_campaign_id": None,
        "show_view_dialog": False,
        "view_campaign_id": None,
        "show_team_assignment": False,
        "team_campaign_id": None,
        "show_role_form_mapping": False,
        "role_form_campaign_id": None,
        "show_evaluation_matrix": False,
        "matrix_campaign_id": None,
        "matrix_group_id": None,
        "show_delete_confirm": False,
        "delete_campaign_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v