import streamlit as st

from ui.pages.campaigns.stepper.session_keys import role_form_key


PLACEHOLDER_LABEL = "— Select a form —"


def render_role_form_selectors(
    campaign_id: int,
    role_names: list[str],
    role_form_map: dict,
    form_options: dict,
    form_id_to_name: dict,
) -> None:
    select_options = [PLACEHOLDER_LABEL] + list(form_options.keys())
    for evaluator_role in role_names:
        with st.expander(f"{evaluator_role} →", expanded=False):
            for evaluatee_role in role_names:
                _render_role_form_selector(
                    campaign_id,
                    evaluator_role,
                    evaluatee_role,
                    role_form_map,
                    form_options,
                    form_id_to_name,
                    select_options,
                )


def _render_role_form_selector(
    campaign_id: int,
    evaluator_role: str,
    evaluatee_role: str,
    role_form_map: dict,
    form_options: dict,
    form_id_to_name: dict,
    select_options: list[str],
) -> None:
    current_form_id = role_form_map.get((evaluator_role, evaluatee_role))
    current_form_name = form_id_to_name.get(current_form_id, PLACEHOLDER_LABEL)
    selected_index = select_options.index(current_form_name) if current_form_name in select_options else 0

    selected_form_name = st.selectbox(
        f"{evaluator_role} → {evaluatee_role}",
        options=select_options,
        index=selected_index,
        key=role_form_key(campaign_id, evaluator_role, evaluatee_role),
    )
    role_form_map[(evaluator_role, evaluatee_role)] = (
        None if selected_form_name == PLACEHOLDER_LABEL else form_options[selected_form_name]
    )
