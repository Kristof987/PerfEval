import streamlit as st

from consts.consts import ICONS
from ui.pages.campaigns.helpers.helpers import get
from ui.pages.campaigns.stepper.session_keys import percentage_input_prefix, percentage_key
from ui.pages.campaigns.steps.reviewers.reviewers_algorithm import auto_assign_reviewers


def render_quick_actions(campaign_id: int, selected_group_id: int, matrix_key: str, members) -> None:
    st.write("---")
    st.write("**Quick Selection:**")

    quick_percentage_key = percentage_key(campaign_id, selected_group_id)
    if quick_percentage_key not in st.session_state:
        st.session_state[quick_percentage_key] = 1

    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

    with col1:
        if st.button(f"{ICONS['select_all']} Select All", use_container_width=True, key=f"stepper_select_all_{matrix_key}"):
            st.session_state[matrix_key] = {
                (int(get(evaluator, "id", 0)), int(get(evaluatee, "id", 0)))
                for evaluator in members
                for evaluatee in members
            }
            st.rerun()

    with col2:
        if st.button(f"{ICONS['delete']} Clear All", use_container_width=True, key=f"stepper_clear_all_{matrix_key}"):
            st.session_state[matrix_key] = set()
            st.rerun()

    with col3:
        percentage = st.number_input(
            "Number of evaluations per Employee",
            min_value=0,
            max_value=max(0, len(members) - 1),
            value=int(st.session_state[quick_percentage_key]),
            step=1,
            key=percentage_input_prefix(quick_percentage_key),
        )
        st.session_state[quick_percentage_key] = percentage

    with col4:
        if st.button(
            f"{ICONS['dice']} Auto-Assign",
            type="primary",
            use_container_width=True,
            key=f"stepper_auto_{matrix_key}",
            help="Automatically creates evaluator→evaluatee pairs based on the selected number per employee. Distributes reviewer load as evenly as possible and avoids duplicate pairs.",
        ):
            member_ids = [int(get(member, "id", 0)) for member in members]
            st.session_state[matrix_key] = auto_assign_reviewers(member_ids, int(percentage))
            st.rerun()

    with col5:
        if st.button(
            f"{ICONS['select_all']} Add self-assessments",
            use_container_width=True,
            key=f"stepper_self_{matrix_key}",
            help="Adds self-evaluation pairs for all team members by selecting each person on their own row/column intersection (employee evaluates themselves).",
        ):
            for member in members:
                mid = int(get(member, "id", 0) or 0)
                st.session_state[matrix_key].add((mid, mid))
            st.rerun()
