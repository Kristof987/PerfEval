import pandas as pd
import streamlit as st

from ui.pages.campaigns.steps.forms.forms_styles import render_forms_help_header


def render_relationship_summary_table(role_names: list[str], role_form_map: dict, form_id_to_name: dict) -> None:
    relationship_rows = []
    for evaluator_role in role_names:
        for evaluatee_role in role_names:
            form_id = role_form_map.get((evaluator_role, evaluatee_role))
            relationship_rows.append(
                {
                    "Evaluator role": evaluator_role,
                    "Evaluatee role": evaluatee_role,
                    "Default form": form_id_to_name.get(form_id, "Not selected"),
                }
            )

    render_forms_help_header()
    st.dataframe(pd.DataFrame(relationship_rows), use_container_width=True, hide_index=True)
