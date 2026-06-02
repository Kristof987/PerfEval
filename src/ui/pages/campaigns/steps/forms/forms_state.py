import streamlit as st

from ui.pages.campaigns.stepper.session_keys import role_form_map_key


def build_default_role_form_map(role_names: list[str]) -> dict[tuple[str, str], int | None]:
    return {
        (evaluator_role, evaluatee_role): None
        for evaluator_role in role_names
        for evaluatee_role in role_names
    }


def merge_role_form_maps(default_map: dict, stored_map: dict, session_map: dict) -> dict:
    merged_map = dict(default_map)
    for source in (stored_map, session_map):
        for pair, form_id in source.items():
            if pair in default_map:
                merged_map[pair] = form_id
    return merged_map


def initialize_role_form_session_map(campaign_id: int, role_names: list[str], stored_map: dict) -> tuple[str, dict]:
    map_key = role_form_map_key(campaign_id)
    default_map = build_default_role_form_map(role_names)
    session_map = st.session_state.get(map_key, {})
    merged_map = merge_role_form_maps(default_map, stored_map, session_map)
    st.session_state[map_key] = merged_map
    return map_key, default_map
