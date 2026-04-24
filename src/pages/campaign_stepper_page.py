from __future__ import annotations

import random
import runpy
from datetime import date, datetime

import pandas as pd
import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService


PHASES = [
    "Create/Edit Campaign",
    "Group Selection",
    "Form Assignments",
    "Reviewer Mapping",
    "Response Collection",
    "Evaluated Campaigns",
    "Close Campaign",
]

PHASE_SHORT = [
    "1. Setup",
    "2. Groups",
    "3. Forms",
    "4. Reviewers",
    "5. Collect",
    "6. Results",
    "7. Close",
]


def _fmt_dt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _to_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text).date()
        except Exception:
            return None
    return None


def _days_left(end_value) -> int | None:
    end_date = _to_date(end_value)
    if not end_date:
        return None
    return (end_date - date.today()).days


def _date_to_dt(d):
    return datetime.combine(d, datetime.min.time()) if d else None


def _get(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _stepper(
    current: int,
    meta_right: str = "",
    lock_future_steps: bool = False,
    state_key: str = "stepper_pills",
    max_enabled_step: int | None = None,
    completed_until: int = -1,
) -> int:
    """
    Modern stepper — st.pills + progress bar.
    Natív Streamlit, nincs JS, nincs oldalújratöltés.
    Kész lépések zöld háttérrel jelennek meg.
    """
    n = len(PHASES)
    pct = int((current / max(n - 1, 1)) * 100)

    # ── CSS: kész lépések zöld háttere (+ opcionális jövőbeli lépés lock) ──
    css_rules = []

    for i in range(max(0, completed_until + 1)):
        css_rules.append(
            f"div[role='radiogroup'] > button:nth-child({i + 1}) {{"
            f"  background-color: #10B981 !important;"
            f"  color: #fff !important;"
            f"  border-color: #10B981 !important;"
            f"}}"
        )

    # Active step highlight (the currently selected/clicked step).
    css_rules.append(
        f"div[role='radiogroup'] > button:nth-child({current + 1}) {{"
        f"  box-shadow: inset 0 0 0 2px rgba(255,255,255,0.88), 0 0 0 3px rgba(16, 185, 129, 0.35), 0 0 0 5px rgba(16, 185, 129, 0.16) !important;"
        f"  border-color: #10B981 !important;"
        f"  transform: translateY(-1px);"
        f"}}"
    )

    if lock_future_steps:
        disable_from = (max_enabled_step + 1) if max_enabled_step is not None else (current + 1)
        for i in range(disable_from, n):
            css_rules.append(
                f"div[role='radiogroup'] > button:nth-child({i + 1}) {{"
                f"  opacity: 0.45 !important;"
                f"  pointer-events: none !important;"
                f"  cursor: default !important;"
                f"}}"
            )

    if css_rules:
        st.markdown(
            f"<style>\n{chr(10).join(css_rules)}\n</style>",
            unsafe_allow_html=True,
        )

    # ── Fejléc: lépés info + határidő ──
    head_left, head_right = st.columns([3, 2])
    with head_left:
        st.markdown(
            f"<p style='margin:0;font-size:14px'>"
            f"<span style='color:#10B981;font-weight:600'>Step {current + 1}</span>"
            f" <span style='color:#aaa'>/ {n}</span>"
            f" <span style='color:#aaa;margin:0 6px'>—</span>"
            f" <span style='font-weight:500'>{PHASES[current]}</span></p>",
            unsafe_allow_html=True,
        )
    with head_right:
        if meta_right:
            st.markdown(
                f"<p style='margin:0;text-align:right;font-size:13px;color:#888'>{meta_right}</p>",
                unsafe_allow_html=True,
            )

    # ── Pill navigáció ──
    def _label(i: int) -> str:
        return PHASE_SHORT[i]

    selected = st.pills(
        "campaign_step",
        options=list(range(n)),
        format_func=_label,
        default=current,
        label_visibility="collapsed",
        key=state_key,
    )

    # ── Progress bar ──
    st.markdown(
        f"""<div style="height:4px;background:#e5e5e0;border-radius:2px;overflow:hidden;margin-top:-0.5rem;margin-bottom:0.35rem">
            <div style="height:100%;width:{pct}%;border-radius:2px;background:linear-gradient(90deg,#10B981,#185FA5)"></div>
        </div>""",
        unsafe_allow_html=True,
    )

    return selected if selected is not None else current


def _render_phase_subpage(phase_index: int) -> None:
    st.markdown("<hr style='margin:0.35rem 0 0.6rem 0;border:none;border-top:1px solid #e6e9ef;'>", unsafe_allow_html=True)
    st.subheader(f"{phase_index + 1}. {PHASES[phase_index]}")
    st.info("This is a placeholder subpage for the selected step.")


def _reset_campaign_navigation_state() -> None:
    st.session_state.show_edit_dialog = False
    st.session_state.edit_campaign_id = None
    st.session_state.show_view_dialog = False
    st.session_state.view_campaign_id = None
    st.session_state.show_team_assignment = False
    st.session_state.team_campaign_id = None
    st.session_state.show_role_form_mapping = False
    st.session_state.role_form_campaign_id = None
    st.session_state.show_evaluation_matrix = False
    st.session_state.matrix_campaign_id = None
    st.session_state.matrix_group_id = None
    st.session_state.show_delete_confirm = False
    st.session_state.delete_campaign_id = None


def _set_step_progress(
    campaign_id,
    completed_phase: int | None = None,
    current_phase: int | None = None,
    force_completed: bool = False,
) -> None:
    if campaign_id == "new" or campaign_id is None:
        return

    phase_key = str(campaign_id)

    completed_by_id = st.session_state.get("campaign_dashboard_completed_phase_by_id", {})
    previous_completed = int(completed_by_id.get(phase_key, -1))
    if completed_phase is not None:
        if force_completed:
            completed_by_id[phase_key] = int(completed_phase)
        else:
            completed_by_id[phase_key] = max(previous_completed, int(completed_phase))
    st.session_state.campaign_dashboard_completed_phase_by_id = completed_by_id

    if completed_phase is not None and int(completed_phase) >= 2:
        invalidated_by_id = st.session_state.get("campaign_dashboard_teams_invalidated_by_id", {})
        invalidated_by_id[phase_key] = False
        st.session_state.campaign_dashboard_teams_invalidated_by_id = invalidated_by_id

    if current_phase is not None:
        phase_by_id = st.session_state.get("campaign_dashboard_phase_by_id", {})
        phase_by_id[phase_key] = int(current_phase)
        st.session_state.campaign_dashboard_phase_by_id = phase_by_id

        # Force pills widget recreation on next run to avoid stale selection
        nonce_by_id = st.session_state.get("campaign_stepper_widget_nonce_by_id", {})
        nonce_by_id[phase_key] = int(nonce_by_id.get(phase_key, 0)) + 1
        st.session_state.campaign_stepper_widget_nonce_by_id = nonce_by_id
        # Clear the pills widget cache so it picks up the new default
        pills_key = f"stepper_pills_{phase_key}"
        if pills_key in st.session_state:
            del st.session_state[pills_key]
        # Signal scroll-to-top after rerun
        st.session_state["_stepper_scroll_to_top"] = True


def _invalidate_after_team_change(campaign_id) -> None:
    if campaign_id == "new" or campaign_id is None:
        return

    phase_key = str(campaign_id)
    invalidated_by_id = st.session_state.get("campaign_dashboard_teams_invalidated_by_id", {})
    invalidated_by_id[phase_key] = True
    st.session_state.campaign_dashboard_teams_invalidated_by_id = invalidated_by_id

    _set_step_progress(campaign_id, completed_phase=1, current_phase=1, force_completed=True)

    # Clear role-form related UI/session caches so removed-group effects are visible immediately.
    keys_to_delete = []
    for key in list(st.session_state.keys()):
        if key == f"stepper_role_form_map_{phase_key}":
            keys_to_delete.append(key)
        elif key == f"role_form_map_{phase_key}":
            keys_to_delete.append(key)
        elif key.startswith(f"stepper_role_form_{phase_key}_"):
            keys_to_delete.append(key)
        elif key.startswith(f"role_form_{phase_key}_"):
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del st.session_state[key]


def _cleanup_on_group_removal(campaign_id: int, group_id: int) -> None:
    """
    When a group is removed from a campaign:
    1. Clear all evaluation matrix assignments for this group
    2. Remove the group from the campaign
    3. Remove role-form defaults for roles that no longer exist in remaining groups
    4. Clean up related session state
    """
    svc = CampaignService()

    # 1. Clear matrix assignments for this group
    try:
        svc.save_evaluations_batch(campaign_id, group_id, [], {})
    except Exception:
        pass

    # 2. Clean up session state for this group's matrix
    matrix_key = f"stepper_matrix_selections_{campaign_id}_{group_id}"
    if matrix_key in st.session_state:
        del st.session_state[matrix_key]
    # Also clean up related editor/percentage keys
    for key in list(st.session_state.keys()):
        if key.startswith(f"stepper_matrix_editor_{matrix_key}"):
            del st.session_state[key]
        elif key == f"stepper_percentage_{campaign_id}_{group_id}":
            del st.session_state[key]
        elif key.startswith(f"stepper_percentage_input_stepper_percentage_{campaign_id}_{group_id}"):
            del st.session_state[key]

    # 3. Remove the group from campaign
    svc.remove_group_from_campaign(campaign_id, group_id)

    # 4. Get remaining roles after removal and clean up orphaned role-form defaults
    remaining_role_names = set(svc.list_campaign_role_names(campaign_id))

    current_defaults = svc.get_role_form_defaults(campaign_id)
    if current_defaults:
        cleaned_defaults = {
            (evaluator_role, evaluatee_role): form_id
            for (evaluator_role, evaluatee_role), form_id in current_defaults.items()
            if evaluator_role in remaining_role_names and evaluatee_role in remaining_role_names
        }
        # Only update if something was actually removed
        if len(cleaned_defaults) != len(current_defaults):
            svc.upsert_role_form_defaults(campaign_id, cleaned_defaults)


def _infer_completed_phase(campaign_obj) -> int:
    campaign_id = int(_get(campaign_obj, "id", 0) or 0)
    if campaign_id <= 0:
        return -1

    try:
        svc = CampaignService()
        groups = svc.list_campaign_groups(campaign_id)
        has_groups = bool(groups)

        has_full_matrix_coverage = False
        if has_groups:
            has_full_matrix_coverage = True
            for group in groups:
                gid = int(_get(group, "id", 0) or 0)
                if gid <= 0:
                    has_full_matrix_coverage = False
                    break
                matrix = svc.get_campaign_group_evaluations(campaign_id, gid)
                has_any_assignment = any(bool(evaluatees) for evaluatees in matrix.values())
                if not has_any_assignment:
                    has_full_matrix_coverage = False
                    break

        evaluations = svc.list_campaign_evaluations(campaign_id)
        has_any_completion = any(str(_get(e, "status", "")).lower() == "completed" for e in evaluations)

        role_defaults = svc.get_role_form_defaults(campaign_id) if has_groups else {}
        has_role_defaults = any(v is not None for v in role_defaults.values()) if role_defaults else False

        has_closed_campaign = not bool(_get(campaign_obj, "is_active", True))

        completed_phase = 0
        if has_groups:
            completed_phase = 1
        if has_role_defaults:
            completed_phase = 2
        if has_full_matrix_coverage:
            completed_phase = 3
        if has_any_completion:
            completed_phase = 4

        invalidated_by_id = st.session_state.get("campaign_dashboard_teams_invalidated_by_id", {})
        if bool(invalidated_by_id.get(str(campaign_id), False)):
            completed_phase = min(completed_phase, 1)

        return completed_phase
    except Exception:
        return 0


def _render_phase_content(phase_index: int, selected_id, campaign_name: str, selected_campaign) -> None:
    if st.session_state.pop("_stepper_scroll_to_top", False):
        import streamlit.components.v1 as components
        components.html(
            "<script>window.parent.document.querySelector('section[data-testid=\"stMain\"]').scrollTo({top: 0});</script>",
            height=0,
        )
    st.markdown("<hr style='margin:0.2rem 0 0.35rem 0;border:none;border-top:1px solid #e6e9ef;'>", unsafe_allow_html=True)

    if phase_index == 0:
        if selected_id == "new":
            st.subheader("Create Campaign")
            with st.form("stepper_create_campaign_form"):
                name = st.text_input("Campaign Name*", placeholder="e.g., Q1 2024 Performance Review")
                description = st.text_area("Description*", placeholder="Enter campaign description")

                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date*", value=datetime.now())
                with col2:
                    end_date = st.date_input("End Date", value=None)

                comment = st.text_area(
                    "Additional Comments (optional)",
                    placeholder="Any additional notes about this campaign",
                )

                submitted = st.form_submit_button("Create Campaign", type="primary", use_container_width=True)

                if submitted:
                    if not name or not description:
                        st.error(f"{ICONS['error']} Please fill in all required fields (marked with *)")
                    else:
                        start_datetime = _date_to_dt(start_date)
                        end_datetime = _date_to_dt(end_date)

                        try:
                            svc = CampaignService()
                            campaign_id = svc.create_campaign(
                                name=name,
                                description=description,
                                start_date=start_datetime,
                                end_date=end_datetime,
                                comment=comment if comment else None,
                            )

                            st.session_state.campaign_dashboard_selected_id = int(campaign_id)
                            _set_step_progress(campaign_id, completed_phase=0, current_phase=1)
                            st.success(f"{ICONS['check']} Campaign '{name}' created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"{ICONS['error']} Failed to create campaign. {e}")
        else:
            st.subheader("Edit Campaign")

            campaign = selected_campaign
            if not campaign:
                st.error("Campaign data is not available.")
                return

            current_name = getattr(campaign, "name", "")
            current_description = getattr(campaign, "description", "") or ""
            start_val = getattr(campaign, "start_date", None)
            current_start = start_val.date() if hasattr(start_val, "date") else start_val
            end_val = getattr(campaign, "end_date", None)
            current_end = end_val.date() if end_val and hasattr(end_val, "date") else end_val
            current_comment = getattr(campaign, "comment", "") or ""
            current_is_active = bool(getattr(campaign, "is_active", True))

            with st.form(f"stepper_edit_campaign_form_{selected_id}"):
                name = st.text_input("Campaign Name*", value=current_name)
                description = st.text_area("Description*", value=current_description)

                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date*", value=current_start)
                with col2:
                    end_date = st.date_input("End Date", value=current_end)

                comment = st.text_area("Additional Comments (optional)", value=current_comment)

                submitted = st.form_submit_button("Save campaign changes", type="primary", use_container_width=True)

                if submitted:
                    if not name or not description:
                        st.error(f"{ICONS['error']} Please fill in all required fields (marked with *)")
                    else:
                        start_datetime = _date_to_dt(start_date)
                        end_datetime = _date_to_dt(end_date)

                        try:
                            svc = CampaignService()
                            svc.update_campaign(
                                campaign_id=int(selected_id),
                                name=name,
                                description=description,
                                start_date=start_datetime,
                                end_date=end_datetime,
                                is_active=current_is_active,
                                comment=comment if comment else None,
                            )
                            _set_step_progress(selected_id, completed_phase=0)
                            st.success(f"{ICONS['check']} Campaign '{name}' updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"{ICONS['error']} Failed to update campaign. {e}")

    elif phase_index == 1:
        st.subheader("Groups")
        st.caption("Group assignment and team creation only")

        if selected_id == "new":
            st.warning("Create the campaign first, then you can assign/create teams.")
            return

        svc = CampaignService()
        campaign_id = int(selected_id)

        all_groups = svc.list_all_groups()
        assigned_groups = svc.list_campaign_groups(campaign_id)
        assigned_group_ids = {int(_get(g, "id", 0) or 0) for g in assigned_groups}

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Create / manage teams", use_container_width=True, key="stepper_open_team_create"):
                st.switch_page("ui/pages/groups/my_groups_page.py")
        with c2:
            if st.button("Continue to Forms", type="primary", use_container_width=True, key="stepper_teams_continue"):
                _set_step_progress(selected_id, completed_phase=1, current_phase=2)
                st.rerun()

        st.write("**Assigned Groups:**")
        if assigned_groups:
            for group in assigned_groups:
                group_id = int(_get(group, "id", 0) or 0)
                if group_id <= 0:
                    continue
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{ICONS.get('office', '🏢')} **{_get(group, 'name', 'Unnamed group')}**")
                with col2:
                    if st.button(ICONS.get("close", "✖"), key=f"stepper_remove_group_{campaign_id}_{group_id}", use_container_width=True):
                        _cleanup_on_group_removal(campaign_id, group_id)
                        _invalidate_after_team_change(selected_id)
                        st.rerun()
        else:
            st.info("No teams assigned yet.")

        st.write("---")
        st.write("**Available Groups:**")
        unassigned_groups = [
            g for g in all_groups if int(_get(g, "id", 0) or 0) not in assigned_group_ids and int(_get(g, "id", 0) or 0) > 0
        ]

        if unassigned_groups:
            for group in unassigned_groups:
                group_id = int(_get(group, "id", 0) or 0)
                if group_id <= 0:
                    continue
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{ICONS.get('office', '🏢')} {_get(group, 'name', 'Unnamed group')}")
                with col2:
                    if st.button(
                        f"{ICONS.get('add', '+')} Add",
                        key=f"stepper_add_group_{campaign_id}_{group_id}",
                        use_container_width=True,
                    ):
                        svc.assign_group_to_campaign(campaign_id, group_id)
                        _invalidate_after_team_change(selected_id)
                        st.rerun()
        else:
            st.info("All teams are already assigned.")

    elif phase_index == 2:
        st.subheader("Forms")
        st.caption("Role-based form assignment")

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

        st.caption("Self-assessment default is '{role} self-assessment' when available.")
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
            if st.button("Save form assignments", type="primary", use_container_width=True, key=f"stepper_forms_save_{campaign_id}"):
                svc.upsert_role_form_defaults(campaign_id, st.session_state[map_key])
                _set_step_progress(selected_id, completed_phase=2, current_phase=3)
                st.success(f"{ICONS['check']} Role-form defaults saved.")
                st.rerun()
        with c_next:
            if st.button("Continue to Matrix", use_container_width=True, key=f"stepper_forms_continue_{campaign_id}"):
                _set_step_progress(selected_id, current_phase=3)
                st.rerun()

    elif phase_index == 3:
        st.subheader("Matrix")
        st.caption("Evaluation matrix only")

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
            str(_get(group, "name", f"Group #{_get(group, 'id', '')}")): int(_get(group, "id", 0) or 0)
            for group in assigned_groups
            if int(_get(group, "id", 0) or 0) > 0
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

        st.write("**Who evaluates whom**")
        st.caption("Rows = person being evaluated (evaluatee) • Columns = person giving evaluation (evaluator)")

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

        st.write("**Manual Selection (Evaluator ↓ / Evaluatee →):**")
        st.caption("Check a cell when the COLUMN person should evaluate the ROW person.")

        matrix_data = {}
        for evaluator in members:
            evaluator_name = str(_get(evaluator, "name", "Unknown"))
            matrix_data[evaluator_name] = []
            for evaluatee in members:
                evaluator_id = int(_get(evaluator, "id", 0) or 0)
                evaluatee_id = int(_get(evaluatee, "id", 0) or 0)
                is_selected = (evaluator_id, evaluatee_id) in st.session_state[matrix_key]
                matrix_data[evaluator_name].append(is_selected)

        df = pd.DataFrame(matrix_data, index=[str(_get(m, "name", "Unknown")) for m in members])

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
                evaluator_name = str(_get(evaluator, "name", "Unknown"))
                if bool(edited_df.iloc[evaluatee_idx][evaluator_name]):
                    st.session_state[matrix_key].add((int(_get(evaluator, "id", 0)), int(_get(evaluatee, "id", 0))))

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
                        st.session_state[matrix_key].add((int(_get(evaluator, "id", 0)), int(_get(evaluatee, "id", 0))))
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
            if st.button(f"{ICONS['dice']} Auto-Assign", type="primary", use_container_width=True, key=f"stepper_auto_{matrix_key}"):
                st.session_state[matrix_key] = set()

                ids = [int(_get(m, "id", 0)) for m in members]
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
            ):
                for member in members:
                    mid = int(_get(member, "id", 0) or 0)
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
                        gid = int(_get(group, "id", 0) or 0)
                        matrix = svc.get_campaign_group_evaluations(campaign_id, gid)
                        has_any_assignment = any(bool(evaluatees) for evaluatees in matrix.values())
                        if not has_any_assignment:
                            all_groups_have_matrix = False
                            break

                    if all_groups_have_matrix:
                        _set_step_progress(selected_id, completed_phase=3, current_phase=4)
                    else:
                        _set_step_progress(selected_id, completed_phase=2, current_phase=4)

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
                _set_step_progress(selected_id, current_phase=4)
                st.rerun()

    elif phase_index == 4:
        st.subheader("Evaluate")
        st.caption("Collect responses and continue when ready")

        svc = CampaignService()
        campaign_id = int(selected_id)
        campaign = svc.get_campaign(campaign_id)
        evaluations = svc.list_campaign_evaluations(campaign_id)

        remaining_by_evaluator: dict[str, int] = {}
        completed_by_evaluator: dict[str, int] = {}
        assigned_by_evaluator: dict[str, int] = {}

        for row in evaluations:
            evaluator_name = str(_get(row, "evaluator_name", "Unknown"))
            status = str(_get(row, "status", "")).lower()

            assigned_by_evaluator[evaluator_name] = assigned_by_evaluator.get(evaluator_name, 0) + 1
            if status == "completed":
                completed_by_evaluator[evaluator_name] = completed_by_evaluator.get(evaluator_name, 0) + 1
            else:
                remaining_by_evaluator[evaluator_name] = remaining_by_evaluator.get(evaluator_name, 0) + 1

        total_remaining = sum(remaining_by_evaluator.values())
        total_assigned = sum(assigned_by_evaluator.values())
        total_completed = sum(completed_by_evaluator.values())

        m1, m2, m3 = st.columns(3)
        m1.metric("Remaining questionnaires", total_remaining)
        m2.metric("Completed questionnaires", total_completed)
        m3.metric("Assigned questionnaires", total_assigned)

        if total_remaining == 0 and total_assigned > 0:
            st.success("All questionnaires are completed.")
        elif total_assigned == 0:
            st.info("No questionnaires assigned yet.")
        else:
            st.warning(f"{total_remaining} questionnaires are still pending.")

        if assigned_by_evaluator:
            rows = []
            for evaluator_name, assigned_count in assigned_by_evaluator.items():
                completed_count = completed_by_evaluator.get(evaluator_name, 0)
                remaining_count = assigned_count - completed_count
                rows.append(
                    {
                        "Employee": evaluator_name,
                        "Remaining": remaining_count,
                        "Completed": completed_count,
                        "Assigned": assigned_count,
                    }
                )

            rows = sorted(rows, key=lambda r: (-r["Remaining"], r["Employee"]))
            st.write("**Remaining questionnaires by employee**")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        if campaign and bool(_get(campaign, "is_active", True)):
            if st.button("Close Form Filling", type="primary", key="stepper_close_filling"):
                try:
                    close_fn = getattr(svc, "close_filling_period", None)
                    if callable(close_fn):
                        close_fn(campaign_id)
                    else:
                        # Backward-compatible fallback if old service instance is loaded
                        with svc.db.transaction() as conn:
                            svc.campaigns.close_filling_period(conn, campaign_id)
                    _set_step_progress(selected_id, completed_phase=4, current_phase=5)
                    st.success("Filling period closed.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"{ICONS['error']} Could not close filling period: {exc}")
        else:
            _set_step_progress(selected_id, current_phase=5)
            st.rerun()

    elif phase_index == 5:
        if selected_id == "new":
            st.warning("Create the campaign first, then open results.")
            return

        # Keep Results marked completed, but do not hard-force current_phase to 5,
        # so the top stepper remains freely clickable to earlier steps.
        _set_step_progress(selected_id, completed_phase=5)
        current_campaign_id = int(selected_id)
        embedded_campaign_key = "cr_embedded_campaign_id"
        last_embedded_campaign_id = st.session_state.get(embedded_campaign_key)

        # Keep internal Campaign Results navigation (campaign/overall/employee)
        # across reruns while staying on this stepper page. Reset only when
        # the selected campaign changes.
        if last_embedded_campaign_id != current_campaign_id:
            st.session_state.cr_view = "campaign"
            st.session_state.cr_selected_employee_id = None
            st.session_state.cr_selected_employee_name = None

        st.session_state[embedded_campaign_key] = current_campaign_id
        st.session_state.cr_selected_campaign_id = current_campaign_id
        st.session_state.cr_selected_campaign_name = campaign_name

        # Render full Campaign Results page content inline (no page navigation).
        runpy.run_path("src/ui/pages/results/campaign_results_page.py", run_name="__main__")

    else:
        st.subheader("Closure")
        st.info("This step is not part of the requested custom routing.")


# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────

st.set_page_config(layout="wide")

if "campaign_dashboard_selected_id" not in st.session_state:
    st.session_state.campaign_dashboard_selected_id = None
if "campaign_dashboard_phase_by_id" not in st.session_state:
    st.session_state.campaign_dashboard_phase_by_id = {}
if "campaign_dashboard_completed_phase_by_id" not in st.session_state:
    st.session_state.campaign_dashboard_completed_phase_by_id = {}
if "campaign_dashboard_teams_invalidated_by_id" not in st.session_state:
    st.session_state.campaign_dashboard_teams_invalidated_by_id = {}
if "campaign_stepper_last_selected_id" not in st.session_state:
    st.session_state.campaign_stepper_last_selected_id = None
if "campaign_stepper_widget_nonce_by_id" not in st.session_state:
    st.session_state.campaign_stepper_widget_nonce_by_id = {}

selected_id = st.session_state.campaign_dashboard_selected_id

if selected_id is None:
    st.info("No campaign selected.")
    st.stop()

campaign_name = "New campaign"
meta_text = "New campaign"
selected_campaign = None

if selected_id != "new":
    svc = CampaignService()
    try:
        campaigns = svc.list_campaigns()
    except Exception as exc:
        st.error(f"Could not load campaign: {exc}")
        st.stop()

    campaign_by_id = {int(getattr(c, "id", 0) or 0): c for c in campaigns}
    selected_campaign = campaign_by_id.get(int(selected_id))

    if selected_campaign is None:
        st.info("Selected campaign no longer exists.")
        st.stop()

    campaign_name = getattr(selected_campaign, "name", "Campaign")
    selected_end_date = getattr(selected_campaign, "end_date", None)
    selected_deadline = _fmt_dt(selected_end_date)
    selected_days_left = _days_left(selected_end_date)
    meta_text = (
        f"Deadline: {selected_deadline} ({selected_days_left} days)"
        if selected_days_left is not None
        else f"Deadline: {selected_deadline}"
    )

st.markdown(f"### Campaign flow — {campaign_name}")

# ── Fázis kezelés ──
phase_by_id = st.session_state.campaign_dashboard_phase_by_id
completed_by_id = st.session_state.campaign_dashboard_completed_phase_by_id
phase_key = str(selected_id)

if phase_key not in completed_by_id:
    if selected_id == "new":
        completed_by_id[phase_key] = -1
    else:
        completed_by_id[phase_key] = _infer_completed_phase(selected_campaign)
    st.session_state.campaign_dashboard_completed_phase_by_id = completed_by_id
elif selected_id != "new":
    inferred_completed = _infer_completed_phase(selected_campaign)
    completed_by_id[phase_key] = max(int(completed_by_id.get(phase_key, -1)), int(inferred_completed))
    st.session_state.campaign_dashboard_completed_phase_by_id = completed_by_id

completed_phase = int(completed_by_id.get(phase_key, -1))
max_enabled_phase = min(len(PHASES) - 1, completed_phase + 1)

# After team changes invalidate downstream green states,
# but still allow moving to the immediate next step (Forms).
invalidated_by_id = st.session_state.get("campaign_dashboard_teams_invalidated_by_id", {})
if bool(invalidated_by_id.get(phase_key, False)):
    max_enabled_phase = max(max_enabled_phase, 2)

current_phase = int(phase_by_id.get(phase_key, 0))

# If we enter an existing campaign from outside this page,
# open directly on the next logical step.
last_selected_id = st.session_state.get("campaign_stepper_last_selected_id")
if selected_id != "new" and str(last_selected_id) != phase_key:
    current_phase = max_enabled_phase
    phase_by_id[phase_key] = current_phase
    st.session_state.campaign_dashboard_phase_by_id = phase_by_id

if current_phase > max_enabled_phase:
    current_phase = max_enabled_phase
    phase_by_id[phase_key] = current_phase
    st.session_state.campaign_dashboard_phase_by_id = phase_by_id

st.session_state.campaign_stepper_last_selected_id = selected_id

# ── Stepper ──
widget_nonce_by_id = st.session_state.get("campaign_stepper_widget_nonce_by_id", {})
widget_nonce = int(widget_nonce_by_id.get(phase_key, 0))
new_phase = _stepper(
    current_phase,
    meta_text,
    lock_future_steps=True,
    state_key=f"stepper_pills_{phase_key}_{widget_nonce}",
    max_enabled_step=max_enabled_phase,
    completed_until=completed_phase,
)

if new_phase != current_phase and new_phase <= max_enabled_phase:
    phase_by_id[phase_key] = new_phase
    st.session_state.campaign_dashboard_phase_by_id = phase_by_id
    st.session_state["_stepper_scroll_to_top"] = True
    st.rerun()

_render_phase_content(current_phase, selected_id, campaign_name, selected_campaign)
