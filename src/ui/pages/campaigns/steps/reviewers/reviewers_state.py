import streamlit as st

from ui.pages.campaigns.helpers.helpers import get
from ui.pages.campaigns.stepper.session_keys import matrix_selections_key


def build_group_options(assigned_groups) -> dict[str, int]:
    return {
        str(get(group, "name", f"Group #{get(group, 'id', '')}")): int(get(group, "id", 0) or 0)
        for group in assigned_groups
        if int(get(group, "id", 0) or 0) > 0
    }


def init_matrix_selection_state(matrix_key: str, evaluation_matrix: dict) -> None:
    if matrix_key in st.session_state:
        return

    st.session_state[matrix_key] = set()
    for evaluator_id in evaluation_matrix:
        for evaluatee_id in evaluation_matrix[evaluator_id]:
            st.session_state[matrix_key].add((evaluator_id, evaluatee_id))


def clear_matrix_selection_state(matrix_key: str) -> None:
    st.session_state.pop(matrix_key, None)


def matrix_key_for(campaign_id: int, group_id: int) -> str:
    return matrix_selections_key(campaign_id, group_id)
