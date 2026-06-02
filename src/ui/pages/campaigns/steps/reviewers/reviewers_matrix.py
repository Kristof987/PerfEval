import pandas as pd
import streamlit as st

from ui.pages.campaigns.helpers.helpers import get
from ui.pages.campaigns.stepper.session_keys import matrix_editor_prefix


def build_matrix_dataframe(members, selections: set[tuple[int, int]]) -> pd.DataFrame:
    matrix_data = {}
    for evaluator in members:
        evaluator_name = str(get(evaluator, "name", "Unknown"))
        matrix_data[evaluator_name] = []
        for evaluatee in members:
            evaluator_id = int(get(evaluator, "id", 0) or 0)
            evaluatee_id = int(get(evaluatee, "id", 0) or 0)
            matrix_data[evaluator_name].append((evaluator_id, evaluatee_id) in selections)

    return pd.DataFrame(matrix_data, index=[str(get(member, "name", "Unknown")) for member in members])


def render_matrix_editor(matrix_key: str, members, selections: set[tuple[int, int]]):
    return st.data_editor(
        build_matrix_dataframe(members, selections),
        use_container_width=True,
        height=min(600, 100 + len(members) * 35),
        hide_index=False,
        key=matrix_editor_prefix(matrix_key),
    )


def read_matrix_dataframe_selection(edited_df, members) -> set[tuple[int, int]]:
    selections = set()
    for evaluatee_idx, evaluatee in enumerate(members):
        for evaluator in members:
            evaluator_name = str(get(evaluator, "name", "Unknown"))
            if bool(edited_df.iloc[evaluatee_idx][evaluator_name]):
                selections.add((int(get(evaluator, "id", 0)), int(get(evaluatee, "id", 0))))
    return selections
