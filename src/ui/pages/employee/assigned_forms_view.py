import streamlit as st


def group_evaluations_by_campaign(evaluations):
    campaigns = {}
    for evaluation in evaluations:
        campaigns.setdefault(evaluation["campaign_name"], []).append(evaluation)
    return campaigns


def render_assigned_forms(evaluations):
    campaigns = group_evaluations_by_campaign(evaluations)

    for campaign_name, items in campaigns.items():
        with st.expander(campaign_name, expanded=True):
            for evaluation in items:
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                with col1:
                    st.write(f"**{evaluation['form_name']}**")
                    st.caption(evaluation.get("form_description") or "")
                with col2:
                    st.write(f"Evaluatee: {evaluation['evaluatee_name']}")
                with col3:
                    st.write(evaluation["status"].capitalize())
                with col4:
                    button_key = f"fill_{evaluation['evaluation_id']}"
                    if st.button(
                        "Fill",
                        key=button_key,
                        disabled=evaluation["status"] == "completed",
                    ):
                        st.session_state.current_evaluation_id = evaluation["evaluation_id"]
                        st.session_state["forms_scroll_to"] = f"eval_form_{evaluation['evaluation_id']}"
                        st.rerun()
