import random
from datetime import datetime

import pandas as pd
import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService

# ----------------------------
# Helpers (robust dict/dataclass access)
# ----------------------------
def _get(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _date_to_dt(d):
    return datetime.combine(d, datetime.min.time()) if d else None


# ----------------------------
# Session init (minimal, keep your existing State.init if you want)
# ----------------------------
_defaults = {
    "show_edit_dialog": False,
    "edit_campaign_id": None,
    "show_view_dialog": False,
    "view_campaign_id": None,
    "show_team_assignment": False,
    "team_campaign_id": None,
    "show_role_form_mapping": False,
    "role_form_campaign_id": None,
    "show_evaluation_matrix": False,
    "matrix_campaign_id": None,
    "matrix_group_id": None,
    "show_delete_confirm": False,
    "delete_campaign_id": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

query_params = st.query_params
svc = CampaignService()

# ----------------------------
# Role -> Role default form mapping (UI-only logic, storage via service)
# ----------------------------
def build_default_role_form_map(role_names, forms):
    if not role_names or not forms:
        return {}

    form_name_to_id = {f["name"]: f["id"] for f in forms}
    default_form_id = forms[0]["id"]

    role_form_map = {}
    for evaluator_role in role_names:
        for evaluatee_role in role_names:
            if evaluator_role == evaluatee_role:
                self_form_name = f"{evaluator_role} self-assessment"
                role_form_map[(evaluator_role, evaluatee_role)] = form_name_to_id.get(self_form_name, default_form_id)
            else:
                role_form_map[(evaluator_role, evaluatee_role)] = default_form_id

    return role_form_map


def ensure_role_form_map(campaign_id, role_names, forms):
    map_key = f"role_form_map_{campaign_id}"
    default_map = build_default_role_form_map(role_names, forms)

    stored_map = svc.get_role_form_defaults(campaign_id)
    session_map = st.session_state.get(map_key, {})
    merged_map = {**default_map, **stored_map, **session_map}

    for pair, form_id in default_map.items():
        if not merged_map.get(pair):
            merged_map[pair] = form_id

    st.session_state[map_key] = merged_map
    svc.upsert_role_form_defaults(campaign_id, merged_map)
    return map_key


# ----------------------------
# Page header
# ----------------------------
st.title(f"{ICONS['dashboard']} Campaign Management")
st.write("Create and manage performance evaluation campaigns")

# ----------------------------
# CREATE (query param)
# ----------------------------
if query_params.get("create") == "true":
    with st.form("create_campaign_form"):
        st.subheader(f"{ICONS['add']} Create New Campaign")

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

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button("Create Campaign", type="primary", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if submitted:
            if not name or not description:
                st.error(f"{ICONS['error']} Please fill in all required fields (marked with *)")
            else:
                start_datetime = _date_to_dt(start_date)
                end_datetime = _date_to_dt(end_date)

                try:
                    campaign_id = svc.create_campaign(
                        name=name,
                        description=description,
                        start_date=start_datetime,
                        end_date=end_datetime,
                        comment=comment if comment else None,
                    )
                    st.success(f"{ICONS['check']} Campaign '{name}' created successfully!")
                    query_params.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"{ICONS['error']} Failed to create campaign. {e}")

        if cancelled:
            query_params.clear()
            st.rerun()

# ----------------------------
# EDIT DIALOG
# ----------------------------
elif st.session_state.show_edit_dialog and st.session_state.edit_campaign_id:
    campaign = svc.get_campaign(st.session_state.edit_campaign_id)

    if campaign:
        with st.form("edit_campaign_form"):
            st.subheader(f"{ICONS['edit']} Edit Campaign: {_get(campaign, 'name')}")

            name = st.text_input("Campaign Name*", value=_get(campaign, "name"))
            description = st.text_area("Description*", value=_get(campaign, "description") or "")

            col1, col2 = st.columns(2)
            with col1:
                start_val = _get(campaign, "start_date")
                current_start = start_val.date() if hasattr(start_val, "date") else start_val
                start_date = st.date_input("Start Date*", value=current_start)
            with col2:
                end_val = _get(campaign, "end_date")
                current_end = end_val.date() if end_val and hasattr(end_val, "date") else end_val
                end_date = st.date_input("End Date", value=current_end)

            is_active = st.checkbox("Active Campaign", value=bool(_get(campaign, "is_active")))
            comment = st.text_area("Additional Comments (optional)", value=_get(campaign, "comment") or "")

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("Update Campaign", type="primary", use_container_width=True)
            with col_cancel:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                if not name or not description:
                    st.error(f"{ICONS['error']} Please fill in all required fields (marked with *)")
                else:
                    start_datetime = _date_to_dt(start_date)
                    end_datetime = _date_to_dt(end_date)

                    try:
                        svc.update_campaign(
                            campaign_id=st.session_state.edit_campaign_id,
                            name=name,
                            description=description,
                            start_date=start_datetime,
                            end_date=end_datetime,
                            is_active=is_active,
                            comment=comment if comment else None,
                        )
                        st.success(f"{ICONS['check']} Campaign '{name}' updated successfully!")
                        st.session_state.show_edit_dialog = False
                        st.session_state.edit_campaign_id = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"{ICONS['error']} Failed to update campaign. {e}")

            if cancelled:
                st.session_state.show_edit_dialog = False
                st.session_state.edit_campaign_id = None
                st.rerun()

# ----------------------------
# VIEW DIALOG
# ----------------------------
elif st.session_state.show_view_dialog and st.session_state.view_campaign_id:
    campaign = svc.get_campaign(st.session_state.view_campaign_id)

    if campaign:
        st.subheader(f"{ICONS['view']} Campaign Details: {_get(campaign, 'name')}")

        col1, col2 = st.columns(2)
        with col1:
            status_icon = ICONS["active"] if _get(campaign, "is_active") else ICONS["inactive"]
            status_text = "Active" if _get(campaign, "is_active") else "Inactive"
            st.write(f"**Status:** {status_icon} {status_text}")
            st.write(f"**Start Date:** {_get(campaign, 'start_date').strftime('%Y-%m-%d')}")
            if _get(campaign, "end_date"):
                st.write(f"**End Date:** {_get(campaign, 'end_date').strftime('%Y-%m-%d')}")
        with col2:
            completed = int(_get(campaign, "completed", 0) or 0)
            total = int(_get(campaign, "total", 0) or 0)
            st.write(f"**Completed:** {completed} / {total}")
            completion_pct = (completed / total * 100) if total > 0 else 0
            st.progress(completion_pct / 100, text=f"Progress: {completion_pct:.0f}%")

        st.write(f"**Description:** {_get(campaign, 'description')}")
        if _get(campaign, "comment"):
            st.write(f"**Comments:** {_get(campaign, 'comment')}")

        st.write("---")
        st.write("**Evaluations:**")
        evaluations = svc.list_campaign_evaluations(st.session_state.view_campaign_id)

        rows = []

        if evaluations:
            for ev in evaluations:
                # ev could be dataclass or dict
                status = _get(ev, "status")
                evaluator_name = _get(ev, "evaluator_name")
                evaluatee_name = _get(ev, "evaluatee_name")
                # Use emoji directly for DataFrame display (ICONS use Streamlit markdown which doesn't render in DataFrame)
                status_icon = {
                    "todo": "\U0001F7E1 Todo",  # 🟡
                    "pending": "\U0001F7E0 Pending",  # 🟠
                    "completed": "\U0001F7E2 Completed"  # 🟢
                }.get(status, "❔")

                rows.append({
                    "Evaluator": _get(ev, "evaluator_name"),
                    "Evaluatee": _get(ev, "evaluatee_name"),
                    "Status": status_icon
                })

            df = pd.DataFrame(rows)

            st.dataframe(df, use_container_width=True)
        else:
            st.info("No evaluations found for this campaign.")

        if st.button("Close", use_container_width=True):
            st.session_state.show_view_dialog = False
            st.session_state.view_campaign_id = None
            st.rerun()

# ----------------------------
# TEAM ASSIGNMENT
# ----------------------------
elif st.session_state.show_team_assignment and st.session_state.team_campaign_id:
    campaign = svc.get_campaign(st.session_state.team_campaign_id)

    if campaign:
        st.subheader(f"{ICONS['teams']} Team Assignment: {_get(campaign, 'name')}")

        all_groups = svc.list_all_groups()
        assigned_groups = svc.list_campaign_groups(st.session_state.team_campaign_id)
        assigned_group_ids = [_get(g, "id") for g in assigned_groups]

        st.write("**Assigned Teams:**")
        if assigned_groups:
            for group in assigned_groups:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"{ICONS.get('office','🏢')} **{_get(group,'name')}**")
                with col2:
                    if st.button(
                        f"{ICONS['matrix']} Matrix",
                        key=f"matrix_{_get(group,'id')}",
                        use_container_width=True,
                    ):
                        st.session_state.show_evaluation_matrix = True
                        st.session_state.matrix_campaign_id = st.session_state.team_campaign_id
                        st.session_state.matrix_group_id = _get(group, "id")
                        st.session_state.show_team_assignment = False
                        st.rerun()
                with col3:
                    if st.button(
                        ICONS["close"],
                        key=f"remove_{_get(group,'id')}",
                        use_container_width=True,
                    ):
                        svc.remove_group_from_campaign(st.session_state.team_campaign_id, _get(group, "id"))
                        st.rerun()
        else:
            st.info("No teams assigned yet.")

        st.write("---")
        st.write("**Available Teams:**")
        unassigned_groups = [g for g in all_groups if _get(g, "id") not in assigned_group_ids]

        if unassigned_groups:
            for group in unassigned_groups:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{ICONS.get('office','🏢')} {_get(group,'name')}")
                with col2:
                    if st.button(
                        f"{ICONS['add']} Add",
                        key=f"add_{_get(group,'id')}",
                        use_container_width=True,
                    ):
                        svc.assign_group_to_campaign(st.session_state.team_campaign_id, _get(group, "id"))
                        st.rerun()
        else:
            st.info("All teams are already assigned.")

        if st.button("Close", use_container_width=True):
            st.session_state.show_team_assignment = False
            st.session_state.team_campaign_id = None
            st.rerun()

# ----------------------------
# ROLE -> ROLE DEFAULT FORMS
# ----------------------------
elif st.session_state.show_role_form_mapping and st.session_state.role_form_campaign_id:
    campaign = svc.get_campaign(st.session_state.role_form_campaign_id)

    if campaign:
        st.subheader(f"{ICONS['matrix']} Role → Role Default Forms: {_get(campaign, 'name')}")
        roles = svc.list_org_roles()
        forms = svc.list_forms()

        if not forms:
            st.error(f"{ICONS['error']} No forms available. Please create an evaluation form first.")
        elif not roles:
            st.error(f"{ICONS['error']} No organisation roles available. Please create roles first.")
        else:
            role_names = [r["name"] for r in roles]
            form_options = {f["name"]: f["id"] for f in forms}
            form_id_to_name = {f["id"]: f["name"] for f in forms}

            map_key = ensure_role_form_map(st.session_state.role_form_campaign_id, role_names, forms)

            st.caption("Self-assessment default is '{role} self-assessment' when available.")
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
                            key=f"role_form_{st.session_state.role_form_campaign_id}_{evaluator_role}_{evaluatee_role}",
                        )
                        st.session_state[map_key][(evaluator_role, evaluatee_role)] = form_options[selected_form_name]

            st.write("---")
            if st.button("Save", type="primary", use_container_width=True):
                svc.upsert_role_form_defaults(st.session_state.role_form_campaign_id, st.session_state[map_key])
                st.success(f"{ICONS['check']} Role-form defaults saved.")

            if st.button("Close", use_container_width=True):
                svc.upsert_role_form_defaults(st.session_state.role_form_campaign_id, st.session_state[map_key])
                st.session_state.show_role_form_mapping = False
                st.session_state.role_form_campaign_id = None
                st.rerun()

# ----------------------------
# EVALUATION MATRIX
# ----------------------------
elif (
    st.session_state.show_evaluation_matrix
    and st.session_state.matrix_campaign_id
    and st.session_state.matrix_group_id
):
    campaign = svc.get_campaign(st.session_state.matrix_campaign_id)
    members = svc.list_group_members(st.session_state.matrix_group_id)
    evaluation_matrix = svc.get_campaign_group_evaluations(
        st.session_state.matrix_campaign_id,
        st.session_state.matrix_group_id,
    )

    matrix_key = f"matrix_selections_{st.session_state.matrix_campaign_id}_{st.session_state.matrix_group_id}"
    if matrix_key not in st.session_state:
        st.session_state[matrix_key] = set()
        for evaluator_id in evaluation_matrix:
            for evaluatee_id in evaluation_matrix[evaluator_id]:
                st.session_state[matrix_key].add((evaluator_id, evaluatee_id))

    if campaign and members:
        group_info = [g for g in svc.list_all_groups() if _get(g, "id") == st.session_state.matrix_group_id]
        group_name = _get(group_info[0], "name") if group_info else "Unknown"

        st.subheader(f"{ICONS['matrix']} Evaluation Matrix: {_get(campaign, 'name')} - {group_name}")
        st.write("**Who evaluates whom**")
        st.caption("Rows = Evaluatee (who receives feedback), Columns = Evaluator (who gives feedback)")

        st.write("---")
        forms = svc.list_forms()
        roles = svc.list_org_roles()

        if not forms:
            st.error(f"{ICONS['error']} No forms available. Please create an evaluation form first.")
        elif not roles:
            st.error(f"{ICONS['error']} No organisation roles available. Please create roles first.")
        else:
            map_key = ensure_role_form_map(
                st.session_state.matrix_campaign_id,
                [r["name"] for r in roles],
                forms,
            )
            st.info("Forms are selected by evaluator role → evaluatee role defaults. Configure them from the campaign list.")
            st.write("---")

            st.write("**Manual Selection (Evaluatee ↓ / Evaluator →):**")
            st.caption("Check the box where row person is evaluated by column person")

            # Build boolean matrix dataframe
            matrix_data = {}
            for evaluator in members:
                evaluator_name = evaluator["name"]
                matrix_data[evaluator_name] = []
                for evaluatee in members:
                    evaluator_id = evaluator["id"]
                    evaluatee_id = evaluatee["id"]
                    is_selected = (evaluator_id, evaluatee_id) in st.session_state[matrix_key]
                    matrix_data[evaluator_name].append(is_selected)

            df = pd.DataFrame(matrix_data, index=[m["name"] for m in members])

            edited_df = st.data_editor(
                df,
                use_container_width=True,
                height=min(600, 100 + len(members) * 35),
                hide_index=False,
                key=f"matrix_editor_{matrix_key}",
            )

            # Persist back to set
            st.session_state[matrix_key] = set()
            for evaluatee_idx, evaluatee in enumerate(members):
                for evaluator_idx, evaluator in enumerate(members):
                    evaluator_name = evaluator["name"]
                    if bool(edited_df.iloc[evaluatee_idx][evaluator_name]):
                        st.session_state[matrix_key].add((evaluator["id"], evaluatee["id"]))

            st.write("---")
            st.write("**Quick Selection:**")

            percentage_key = f"percentage_{st.session_state.matrix_campaign_id}_{st.session_state.matrix_group_id}"
            if percentage_key not in st.session_state:
                st.session_state[percentage_key] = 1

            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

            with col1:
                if st.button(f"{ICONS['select_all']} Select All", use_container_width=True):
                    st.session_state[matrix_key] = set()
                    for evaluator in members:
                        for evaluatee in members:
                            st.session_state[matrix_key].add((evaluator["id"], evaluatee["id"]))
                    st.rerun()

            with col2:
                if st.button(f"{ICONS['delete']} Clear All", use_container_width=True):
                    st.session_state[matrix_key] = set()
                    st.rerun()

            with col3:
                # TODO: rename percentage_key since it is no longer a percentage
                percentage = st.number_input(
                    "Number of evaluations per Employee",
                    min_value=0,
                    max_value=max(0, len(members) - 1),
                    value=int(st.session_state[percentage_key]),
                    step=1,
                    key=f"percentage_input_{percentage_key}",
                )
                st.session_state[percentage_key] = percentage

            with col4:
                if st.button(f"{ICONS['dice']} Auto-Assign", type="primary", use_container_width=True):
                    st.session_state[matrix_key] = set()

                    ids = [m["id"] for m in members]
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
                if st.button(f"{ICONS['select_all']} Add self-assessments", use_container_width=True):
                    for member in members:
                        st.session_state[matrix_key].add((member["id"], member["id"]))
                    st.rerun()

            st.write("---")

            col_save, col_back = st.columns(2)
            with col_save:
                if st.button(f"{ICONS['save']} Save Evaluations", type="primary", use_container_width=True):
                    assignments = list(st.session_state[matrix_key])
                    role_form_map = st.session_state.get(map_key, {}) if roles and forms else {}

                    # Check missing roles BEFORE save (same UX as your old code)
                    all_employee_ids = list({eid for pair in assignments for eid in pair})
                    # Service validates too, but we keep the same "pretty error message" here:
                    # We reuse service's employee role map? If you want that, add svc.get_employee_roles_map(...)
                    # For now we do lightweight check by attempting save; if it errors, show message.
                    result = svc.save_evaluations_batch(
                        st.session_state.matrix_campaign_id,
                        st.session_state.matrix_group_id,
                        assignments,
                        role_form_map,
                    )

                    if result.success:
                        st.success(
                            f"{ICONS['check']} Saved {len(assignments)} evaluation assignments with role-based forms!"
                        )
                        if matrix_key in st.session_state:
                            del st.session_state[matrix_key]
                        st.rerun()
                    else:
                        detail = f" Details: {result.error}" if result.error else ""
                        st.error(f"{ICONS['error']} Failed to save evaluations.{detail}")

            with col_back:
                if st.button("Back to Teams", use_container_width=True):
                    if matrix_key in st.session_state:
                        del st.session_state[matrix_key]
                    st.session_state.show_evaluation_matrix = False
                    st.session_state.show_team_assignment = True
                    st.session_state.matrix_group_id = None
                    st.rerun()

# ----------------------------
# DELETE CONFIRM
# ----------------------------
elif st.session_state.show_delete_confirm and st.session_state.delete_campaign_id:
    campaign = svc.get_campaign(st.session_state.delete_campaign_id)

    if campaign:
        st.warning(f"{ICONS['warning']} Are you sure you want to delete campaign '{_get(campaign,'name')}'?")
        st.write("This will also delete all associated evaluations. This action cannot be undone.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete", type="primary", use_container_width=True):
                try:
                    svc.delete_campaign(st.session_state.delete_campaign_id)
                    st.success(f"{ICONS['check']} Campaign deleted successfully!")
                    st.session_state.show_delete_confirm = False
                    st.session_state.delete_campaign_id = None
                    st.rerun()
                except Exception as e:
                    st.error(f"{ICONS['error']} Failed to delete campaign. {e}")
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_delete_confirm = False
                st.session_state.delete_campaign_id = None
                st.rerun()

# ----------------------------
# DEFAULT LIST VIEW
# ----------------------------
else:
    st.write("")
    if st.button(f"{ICONS['add']} Create New Campaign", type="primary", use_container_width=True):
        query_params["create"] = "true"
        st.rerun()

    st.write("")
    st.write("---")
    st.subheader("Campaign List")

    campaigns = svc.list_campaigns()

    if not campaigns:
        st.info(f"{ICONS.get('list','📋')} No campaigns found. Create your first campaign to get started!")
    else:
        for campaign in campaigns:
            completed = int(_get(campaign, "completed", 0) or 0)
            total = int(_get(campaign, "total", 0) or 0)
            completion_pct = (completed / total * 100) if total > 0 else 0

            status_icon = ICONS["active"] if _get(campaign, "is_active") else ICONS["inactive"]
            status_text = "ACTIVE" if _get(campaign, "is_active") else "INACTIVE"

            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.write(f"### {_get(campaign,'name')}")
                    start_str = _get(campaign, "start_date").strftime("%Y-%m-%d")
                    end_dt = _get(campaign, "end_date")
                    end_str = end_dt.strftime("%Y-%m-%d") if end_dt else "N/A"
                    st.caption(f"Start: {start_str} | End: {end_str}")

                with col2:
                    st.write("")
                    st.write(f"{status_icon} **{status_text}**")

                with col3:
                    st.write("")
                    st.write(f"**{completed}/{total}**")

                st.progress(completion_pct / 100, text=f"Completion: {completion_pct:.0f}%")

                col_view, col_edit, col_teams, col_role_forms, col_toggle, col_delete = st.columns(
                    [1, 1, 1, 1, 1, 1]
                )

                with col_view:
                    if st.button(f"{ICONS['view']} View", key=f"view_{_get(campaign,'id')}", use_container_width=True):
                        st.session_state.show_view_dialog = True
                        st.session_state.view_campaign_id = _get(campaign, "id")
                        st.rerun()

                with col_edit:
                    if _get(campaign, "is_active"):
                        if st.button(
                            f"{ICONS['edit']} Edit",
                            key=f"edit_{_get(campaign,'id')}",
                            use_container_width=True,
                        ):
                            st.session_state.show_edit_dialog = True
                            st.session_state.edit_campaign_id = _get(campaign, "id")
                            st.rerun()
                    else:
                        st.button(
                            f"{ICONS['edit']} Edit",
                            key=f"edit_{_get(campaign,'id')}",
                            disabled=True,
                            use_container_width=True,
                        )

                with col_teams:
                    if st.button(
                        f"{ICONS['teams']} Groups",
                        key=f"teams_{_get(campaign,'id')}",
                        use_container_width=True,
                    ):
                        roles = svc.list_org_roles()
                        forms = svc.list_forms()
                        if roles and forms:
                            ensure_role_form_map(_get(campaign, "id"), [r["name"] for r in roles], forms)
                        st.session_state.show_team_assignment = True
                        st.session_state.team_campaign_id = _get(campaign, "id")
                        st.rerun()

                with col_role_forms:
                    if st.button(
                        f"{ICONS['matrix']} Assign forms",
                        key=f"role_forms_{_get(campaign,'id')}",
                        use_container_width=True,
                    ):
                        st.session_state.show_role_form_mapping = True
                        st.session_state.role_form_campaign_id = _get(campaign, "id")
                        st.rerun()

                with col_toggle:
                    toggle_icon = ICONS["pause"] if _get(campaign, "is_active") else ICONS["play"]
                    toggle_label = (
                        f"{toggle_icon} Deactivate" if _get(campaign, "is_active") else f"{toggle_icon} Activate"
                    )
                    if st.button(toggle_label, key=f"toggle_{_get(campaign,'id')}", use_container_width=True):
                        try:
                            svc.toggle_campaign(_get(campaign, "id"))
                            st.rerun()
                        except Exception as e:
                            st.error(f"{ICONS['error']} Toggle failed: {e}")

                with col_delete:
                    if st.button(
                        f"{ICONS['delete']} Delete",
                        key=f"delete_{_get(campaign,'id')}",
                        use_container_width=True,
                    ):
                        st.session_state.show_delete_confirm = True
                        st.session_state.delete_campaign_id = _get(campaign, "id")
                        st.rerun()

                st.write("---")

st.write("")
st.info(f"{ICONS['lightbulb']} **Tip:** Use the Teams button to assign groups and configure evaluation matrices for each campaign.")