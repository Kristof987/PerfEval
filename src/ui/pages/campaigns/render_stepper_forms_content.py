import streamlit as st
import pandas as pd

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.common.common import set_step_progress


def render_forms(selected_id):
    st.subheader("Forms")
    st.caption("Role-based form assignment")
    status_placeholder = st.empty()
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

    placeholder_label = "— Select a form —"
    form_options = {f["name"]: f["id"] for f in forms}
    form_id_to_name = {f["id"]: f["name"] for f in forms}
    map_key = f"stepper_role_form_map_{campaign_id}"

    default_map = {}
    for evaluator_role in role_names:
        for evaluatee_role in role_names:
            default_map[(evaluator_role, evaluatee_role)] = None

    stored_map = svc.get_role_form_defaults(campaign_id)
    session_map = st.session_state.get(map_key, {})

    merged_map = dict(default_map)
    for source in (stored_map, session_map):
        for pair, form_id in source.items():
            if pair in default_map:
                merged_map[pair] = form_id

    st.session_state[map_key] = merged_map

    total_pairs = len(default_map)

    st.write("---")

    relationship_rows = []
    for evaluator_role in role_names:
        for evaluatee_role in role_names:
            form_id = st.session_state[map_key].get((evaluator_role, evaluatee_role))
            relationship_rows.append(
                {
                    "Evaluator role": evaluator_role,
                    "Evaluatee role": evaluatee_role,
                    "Default form": form_id_to_name.get(form_id, "Not selected"),
                }
            )

    st.markdown(
        """
        <style>
            .forms-help-wrap { position: relative; display: inline-flex; align-items: center; }
            .forms-help-icon {
                display:inline-flex;align-items:center;justify-content:center;
                width:20px;height:20px;border:1px solid #bfdbfe;background:#eff6ff;color:#1d4ed8;
                border-radius:999px;font-size:12px;font-weight:700;line-height:1;
                box-shadow:0 1px 2px rgba(15,23,42,0.08);cursor:default;
            }
            .forms-help-tooltip {
                position:absolute;left:50%;transform:translateX(-50%);top:28px;
                min-width:260px;max-width:340px;padding:8px 10px;
                background:#0f172a;color:#f8fafc;border-radius:8px;
                font-size:12px;line-height:1.35;box-shadow:0 6px 20px rgba(15,23,42,0.25);
                opacity:0;visibility:hidden;transition:opacity .14s ease, transform .14s ease;
                pointer-events:none;z-index:20;
            }
            .forms-help-wrap:hover .forms-help-tooltip {
                opacity:1;visibility:visible;transform:translateX(-50%) translateY(2px);
            }
        </style>
        <div style='display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 0 6px 0;'>
            <div style='display:flex;align-items:center;gap:8px;'>
                <strong>Available role relationships in this campaign:</strong>
                <span class='forms-help-wrap'>
                    <span class='forms-help-icon'>?</span>
                    <span class='forms-help-tooltip'>Each row is an evaluator role → evaluatee role pair that needs a selected default form.</span>
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(pd.DataFrame(relationship_rows), use_container_width=True, hide_index=True)
    st.write("---")

    for evaluator_role in role_names:
        with st.expander(f"{evaluator_role} →", expanded=False):
            for evaluatee_role in role_names:
                current_form_id = st.session_state[map_key].get((evaluator_role, evaluatee_role))
                current_form_name = form_id_to_name.get(current_form_id, placeholder_label)
                select_options = [placeholder_label] + list(form_options.keys())
                selected_index = select_options.index(current_form_name) if current_form_name in select_options else 0

                selected_form_name = st.selectbox(
                    f"{evaluator_role} → {evaluatee_role}",
                    options=select_options,
                    index=selected_index,
                    key=f"stepper_role_form_{campaign_id}_{evaluator_role}_{evaluatee_role}",
                )
                st.session_state[map_key][(evaluator_role, evaluatee_role)] = (
                    None if selected_form_name == placeholder_label else form_options[selected_form_name]
                )

    selected_pairs = sum(1 for _, form_id in st.session_state[map_key].items() if form_id)
    if selected_pairs == total_pairs and total_pairs > 0:
        status_placeholder.markdown(
            f"""
            <div style='border:1px solid #86efac;background:#f0fdf4;color:#166534;border-radius:10px;padding:10px 12px;margin:4px 0 10px 0;'>
                <span style='font-size:14px;font-weight:600;'>✅ Default form assignment ready</span><br>
                <span style='font-size:12px;color:#166534;'>{selected_pairs}/{total_pairs} role relationships are mapped.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        status_placeholder.markdown(
            f"""
            <div style='border:1px solid #fecaca;background:#fef2f2;color:#991b1b;border-radius:10px;padding:10px 12px;margin:4px 0 10px 0;'>
                <span style='font-size:14px;font-weight:600;'>❌ Missing default form assignments</span><br>
                <span style='font-size:12px;color:#7f1d1d;'>{selected_pairs}/{total_pairs} role relationships are mapped. Please complete all before saving.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("---")
    c_save, c_next = st.columns([1, 1])
    with c_save:
        if st.button("Save form assignments", type="primary", use_container_width=True,
                     key=f"stepper_forms_save_{campaign_id}"):
            missing_pairs = [
                f"{ev} → {ee}"
                for (ev, ee), form_id in st.session_state[map_key].items()
                if not form_id
            ]
            if missing_pairs:
                st.error(
                    f"{ICONS['error']} Please select a form for every role pair before saving. "
                    f"Missing: {', '.join(missing_pairs[:8])}"
                    + (" ..." if len(missing_pairs) > 8 else "")
                )
                return
            svc.upsert_role_form_defaults(campaign_id, st.session_state[map_key])
            set_step_progress(selected_id, completed_phase=2, current_phase=3)
            st.success(f"{ICONS['check']} Role-form defaults saved.")
            st.rerun()
    with c_next:
        if st.button("Continue to Matrix", use_container_width=True, key=f"stepper_forms_continue_{campaign_id}"):
            set_step_progress(selected_id, current_phase=3)
            st.rerun()
