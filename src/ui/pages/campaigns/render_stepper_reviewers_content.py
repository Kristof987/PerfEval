import random

import pandas as pd
import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.common.common import set_step_progress
from ui.pages.campaigns.helpers.helpers import get


def render_reviewers(selected_id):
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

    group_options = {
        str(get(group, "name", f"Group #{get(group, 'id', '')}")): int(get(group, "id", 0) or 0)
        for group in assigned_groups
        if int(get(group, "id", 0) or 0) > 0
    }

    if not group_options:
        st.warning("No valid team found for matrix configuration.")
        return

    selected_group_name = st.selectbox(
        "Team",
        options=list(group_options.keys()),
        key=f"stepper_matrix_group_{selected_id}",
    )
    selected_group_id = int(group_options[selected_group_name])

    members = svc.list_group_members(selected_group_id)
    evaluation_matrix = svc.get_campaign_group_evaluations(campaign_id, selected_group_id)

    matrix_key = f"stepper_matrix_selections_{campaign_id}_{selected_group_id}"
    if matrix_key not in st.session_state:
        st.session_state[matrix_key] = set()
        for evaluator_id in evaluation_matrix:
            for evaluatee_id in evaluation_matrix[evaluator_id]:
                st.session_state[matrix_key].add((evaluator_id, evaluatee_id))

    if not members:
        st.info("No members found in this team.")
        return

    st.info(
        "Rows represent employees being evaluated, columns represent evaluators.\n"
        "Select a cell to assign an evaluation relationship."
    )

    forms = svc.list_forms()
    role_names = svc.list_campaign_role_names(campaign_id)

    if not forms:
        st.error(f"{ICONS['error']} No forms available. Please create an evaluation form first.")
        return

    if not role_names:
        st.error(
            f"{ICONS['error']} No campaign roles available. "
            "Assign groups and roles before creating evaluations."
        )
        return


    matrix_data = {}
    for evaluator in members:
        evaluator_name = str(get(evaluator, "name", "Unknown"))
        matrix_data[evaluator_name] = []
        for evaluatee in members:
            evaluator_id = int(get(evaluator, "id", 0) or 0)
            evaluatee_id = int(get(evaluatee, "id", 0) or 0)
            is_selected = (evaluator_id, evaluatee_id) in st.session_state[matrix_key]
            matrix_data[evaluator_name].append(is_selected)

    df = pd.DataFrame(matrix_data, index=[str(get(m, "name", "Unknown")) for m in members])

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        height=min(600, 100 + len(members) * 35),
        hide_index=False,
        key=f"stepper_matrix_editor_{matrix_key}",
    )

    st.session_state[matrix_key] = set()
    for evaluatee_idx, evaluatee in enumerate(members):
        for evaluator_idx, evaluator in enumerate(members):
            evaluator_name = str(get(evaluator, "name", "Unknown"))
            if bool(edited_df.iloc[evaluatee_idx][evaluator_name]):
                    st.session_state[matrix_key].add((int(get(evaluator, "id", 0)), int(get(evaluatee, "id", 0))))

    selected_pairs = len(st.session_state[matrix_key])
    if selected_pairs > 0:
        status_placeholder.markdown(
            f"""
            <div style='border:1px solid #86efac;background:#f0fdf4;color:#166534;border-radius:10px;padding:10px 12px;margin:4px 0 10px 0;'>
                <span style='font-size:14px;font-weight:600;'>✅ Matrix has assignments</span><br>
                <span style='font-size:12px;color:#166534;'>{selected_pairs} evaluation pair(s) selected.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        status_placeholder.markdown(
            """
            <div style='border:1px solid #fecaca;background:#fef2f2;color:#991b1b;border-radius:10px;padding:10px 12px;margin:4px 0 10px 0;'>
                <span style='font-size:14px;font-weight:600;'>❌ Matrix is empty</span><br>
                <span style='font-size:12px;color:#7f1d1d;'>Select at least one evaluation pair before saving.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("---")
    st.write("**Quick Selection:**")

    percentage_key = f"stepper_percentage_{campaign_id}_{selected_group_id}"
    if percentage_key not in st.session_state:
        st.session_state[percentage_key] = 1

    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

    with col1:
        if st.button(f"{ICONS['select_all']} Select All", use_container_width=True, key=f"stepper_select_all_{matrix_key}"):
            st.session_state[matrix_key] = set()
            for evaluator in members:
                for evaluatee in members:
                    st.session_state[matrix_key].add((int(get(evaluator, "id", 0)), int(get(evaluatee, "id", 0))))
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
            value=int(st.session_state[percentage_key]),
            step=1,
            key=f"stepper_percentage_input_{percentage_key}",
        )
        st.session_state[percentage_key] = percentage

    with col4:
        if st.button(
            f"{ICONS['dice']} Auto-Assign",
            type="primary",
            use_container_width=True,
            key=f"stepper_auto_{matrix_key}",
            help="Automatically creates evaluator→evaluatee pairs based on the selected number per employee. Distributes reviewer load as evenly as possible and avoids duplicate pairs.",
        ):
            st.session_state[matrix_key] = set()

            ids = [int(get(m, "id", 0)) for m in members]
            k = int(percentage)

            out = {i: 0 for i in ids}
            pool = [evaluatee for evaluatee in ids for _ in range(k)]
            random.shuffle(pool)

            for evaluatee in pool:
                candidates = [
                    evaluator
                    for evaluator in ids
                    if evaluator != evaluatee and (evaluator, evaluatee) not in st.session_state[matrix_key]
                ]
                if not candidates:
                    continue

                min_out = min(out[e] for e in candidates)
                best = [e for e in candidates if out[e] == min_out]
                evaluator = random.choice(best)

                st.session_state[matrix_key].add((evaluator, evaluatee))
                out[evaluator] += 1

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

    st.write("---")

    c_save, c_reload, c_next = st.columns([1, 1, 1])
    with c_save:
        if st.button(f"{ICONS['save']} Save Matrix", type="primary", use_container_width=True, key=f"stepper_save_{matrix_key}"):
            assignments = list(st.session_state[matrix_key])
            result = svc.save_evaluations_batch(campaign_id, selected_group_id, assignments, {})

            if result.success:
                groups = svc.list_campaign_groups(campaign_id)
                all_groups_have_matrix = bool(groups)
                for group in groups:
                    gid = int(get(group, "id", 0) or 0)
                    matrix = svc.get_campaign_group_evaluations(campaign_id, gid)
                    has_any_assignment = any(bool(evaluatees) for evaluatees in matrix.values())
                    if not has_any_assignment:
                        all_groups_have_matrix = False
                        break

                if all_groups_have_matrix:
                    set_step_progress(selected_id, completed_phase=3, current_phase=4)
                else:
                    set_step_progress(selected_id, completed_phase=2, current_phase=4)

                if matrix_key in st.session_state:
                    del st.session_state[matrix_key]
                st.success(f"{ICONS['check']} Saved {len(assignments)} evaluation assignments.")
                st.rerun()
            else:
                detail = f" Details: {result.error}" if result.error else ""
                st.error(f"{ICONS['error']} Failed to save evaluations.{detail}")

    with c_reload:
        if st.button("Reload saved matrix", use_container_width=True, key=f"stepper_reload_{matrix_key}"):
            if matrix_key in st.session_state:
                del st.session_state[matrix_key]
            st.rerun()

    with c_next:
        if st.button("Continue to Evaluate", use_container_width=True, key=f"stepper_matrix_continue_{campaign_id}"):
            set_step_progress(selected_id, completed_phase=3, current_phase=4)
            st.rerun()
