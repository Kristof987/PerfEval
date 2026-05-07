import streamlit as st
import pandas as pd

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.common.common import set_step_progress


def render_forms(selected_id):
    st.subheader("Forms")
    st.caption("Role-based form assignment")
    st.info(
        "Assign a default form for each evaluator → evaluatee role pair. "
        "These defaults are used when creating evaluations in this campaign."
    )
    if st.button("Create / manage forms", use_container_width=True, key="stepper_open_form_builder"):
        st.switch_page("ui/pages/forms/form_builder_page.py")

    if selected_id == "new":
        st.warning("Create the campaign first, then select forms.")
        return

    svc = CampaignService()
    campaign_id = int(selected_id)
    role_names = svc.list_campaign_role_names(campaign_id)
    forms = svc.list_forms()

    if not forms:
        st.error(f"{ICONS['error']} No forms available. Please create an evaluation form first.")
        return

    if not role_names:
        st.error(
            f"{ICONS['error']} No campaign roles available yet. "
            "Assign groups to this campaign and make sure employees have organisation roles."
        )
        return

    form_options = {f["name"]: f["id"] for f in forms}
    form_id_to_name = {f["id"]: f["name"] for f in forms}
    map_key = f"stepper_role_form_map_{campaign_id}"

    default_form_id = forms[0]["id"]
    default_map = {}
    for evaluator_role in role_names:
        for evaluatee_role in role_names:
            if evaluator_role == evaluatee_role:
                self_form_name = f"{evaluator_role} self-assessment"
                default_map[(evaluator_role, evaluatee_role)] = form_options.get(self_form_name, default_form_id)
            else:
                default_map[(evaluator_role, evaluatee_role)] = default_form_id

    stored_map = svc.get_role_form_defaults(campaign_id)
    session_map = st.session_state.get(map_key, {})

    merged_map = dict(default_map)
    for source in (stored_map, session_map):
        for pair, form_id in source.items():
            if pair in default_map and form_id:
                merged_map[pair] = form_id

    st.session_state[map_key] = merged_map
    st.write("---")

    relationship_rows = []
    for evaluator_role in role_names:
        for evaluatee_role in role_names:
            form_id = st.session_state[map_key].get((evaluator_role, evaluatee_role))
            relationship_rows.append(
                {
                    "Evaluator role": evaluator_role,
                    "Evaluatee role": evaluatee_role,
                    "Default form": form_id_to_name.get(form_id, "N/A"),
                }
            )

    st.write("**Available role relationships in this campaign:**")
    st.dataframe(pd.DataFrame(relationship_rows), use_container_width=True, hide_index=True)
    st.write("---")

    for evaluator_role in role_names:
        with st.expander(f"{evaluator_role} →", expanded=False):
            for evaluatee_role in role_names:
                current_form_id = st.session_state[map_key].get((evaluator_role, evaluatee_role))
                fallback_name = list(form_options.keys())[0]
                current_form_name = form_id_to_name.get(current_form_id, fallback_name)

                selected_form_name = st.selectbox(
                    f"{evaluator_role} → {evaluatee_role}",
                    options=list(form_options.keys()),
                    index=list(form_options.keys()).index(current_form_name),
                    key=f"stepper_role_form_{campaign_id}_{evaluator_role}_{evaluatee_role}",
                )
                st.session_state[map_key][(evaluator_role, evaluatee_role)] = form_options[selected_form_name]

    st.write("---")
    c_save, c_next = st.columns([1, 1])
    with c_save:
        if st.button("Save form assignments", type="primary", use_container_width=True,
                     key=f"stepper_forms_save_{campaign_id}"):
            svc.upsert_role_form_defaults(campaign_id, st.session_state[map_key])
            set_step_progress(selected_id, completed_phase=2, current_phase=3)
            st.success(f"{ICONS['check']} Role-form defaults saved.")
            st.rerun()
    with c_next:
        if st.button("Continue to Matrix", use_container_width=True, key=f"stepper_forms_continue_{campaign_id}"):
            set_step_progress(selected_id, current_phase=3)
            st.rerun()
