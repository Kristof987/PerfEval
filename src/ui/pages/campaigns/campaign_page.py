import random
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

try:
    import streamlit_shadcn_ui as ui
except ModuleNotFoundError:
    ui = None

try:
    from streamlit_extras.scroll_to_element import scroll_to_element
except ModuleNotFoundError:
    scroll_to_element = None

try:
    from streamlit_extras.scroll_to_element import _SCROLL_COMPONENT, _key_to_class_name
except Exception:
    _SCROLL_COMPONENT = None
    _key_to_class_name = None

try:
    from streamlit_extras.steps import steps as steps_component
except ModuleNotFoundError:
    steps_component = None

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


def _list_campaign_role_names(campaign_id: int):
    """Roles currently present among employees in groups assigned to this campaign."""
    campaign_groups = svc.list_campaign_groups(campaign_id)
    group_ids = [_get(g, "id") for g in campaign_groups if _get(g, "id") is not None]

    employee_ids = set()
    for group_id in group_ids:
        members = svc.list_group_members(group_id)
        for member in members:
            employee_id = _get(member, "id")
            if employee_id is not None:
                employee_ids.add(int(employee_id))

    if not employee_ids:
        return []

    with svc.db.connection() as conn:
        roles_map = svc.employees.get_roles_map(conn, list(employee_ids))

    return sorted({role for role in roles_map.values() if role})


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
    "selected_campaign_id": None,
    "scroll_to_selected_campaign": False,
    "scroll_request_id": 0,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

query_params = st.query_params
svc = CampaignService()

_CAMPAIGN_FLASH_KEY = "campaign_page_success_message"
_campaign_flash = st.session_state.pop(_CAMPAIGN_FLASH_KEY, None)
if _campaign_flash:
    st.success(_campaign_flash)
    st.markdown(
        """
        <script>
        setTimeout(() => {
          const alerts = window.parent.document.querySelectorAll('[data-testid="stAlert"]');
          alerts.forEach(a => { a.style.display = 'none'; });
        }, 3500);
        </script>
        """,
        unsafe_allow_html=True,
    )


def _campaign_flash_success_and_rerun(message: str) -> None:
    st.session_state[_CAMPAIGN_FLASH_KEY] = message
    st.rerun()


def _scroll_to_element_force(key: str) -> None:
    if not key:
        return

    if _SCROLL_COMPONENT is not None and _key_to_class_name is not None:
        request_id = int(st.session_state.get("scroll_request_id", 0)) + 1
        st.session_state.scroll_request_id = request_id

        with st._event:
            _SCROLL_COMPONENT(
                data={
                    "class_name": _key_to_class_name(key),
                    "scroll_mode": "smooth",
                    "alignment": "start",
                    "request_id": request_id,
                },
                width="stretch",
                height=0,
                key=f"scroll_to_request_{request_id}",
            )
        return

    if scroll_to_element is not None:
        scroll_to_element(key, scroll_mode="smooth", alignment="start")


def _to_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _to_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.max.time())
    return None


def _format_deadline(end_value):
    end_dt = _to_datetime(end_value)
    if end_dt is None:
        return "No deadline", "#64748b", None

    if end_dt.tzinfo is not None and end_dt.tzinfo.utcoffset(end_dt) is not None:
        now = datetime.now(end_dt.tzinfo)
    else:
        now = datetime.now()
    remaining_seconds = int((end_dt - now).total_seconds())

    if remaining_seconds < 0:
        return "Expired", "#b91c1c", remaining_seconds

    days = remaining_seconds // 86400
    hours = (remaining_seconds % 86400) // 3600
    minutes = (remaining_seconds % 3600) // 60

    if remaining_seconds >= 7 * 86400:
        label = f"{days} days"
    elif remaining_seconds >= 86400:
        label = f"{days} days {hours} hours"
    elif remaining_seconds >= 3600:
        label = f"{hours} hours {minutes} minutes"
    else:
        label = f"0 hours {minutes} minutes"

    return label, "#334155", remaining_seconds


def _campaign_status_meta(campaign, completed: int, total: int):
    today = date.today()
    end_date = _to_date(_get(campaign, "end_date"))
    is_active = bool(_get(campaign, "is_active"))
    comment = str(_get(campaign, "comment") or "")
    is_pending_results = "[PENDING_RESULTS]" in comment
    completion_pct = (completed / total * 100) if total > 0 else 0

    if end_date and end_date < today:
        return {
            "label": "CLOSED",
            "fg": "#991b1b",
            "bg": "#fee2e2",
            "rank": 4,
            "completion_pct": completion_pct,
        }

    if is_pending_results:
        return {
            "label": "PENDING RESULTS",
            "fg": "#7c2d12",
            "bg": "#ffedd5",
            "rank": 2,
            "completion_pct": completion_pct,
        }

    if is_active:
        return {
            "label": "ACTIVE",
            "fg": "#065f46",
            "bg": "#d1fae5",
            "rank": 1,
            "completion_pct": completion_pct,
        }

    return {
        "label": "INACTIVE",
        "fg": "#334155",
        "bg": "#e2e8f0",
        "rank": 3,
        "completion_pct": completion_pct,
    }


def _status_badge_html(label: str, fg: str, bg: str) -> str:
    return (
        f"<span style='display:inline-block;padding:0.2rem 0.55rem;border-radius:9999px;"
        f"font-size:0.76rem;font-weight:700;color:{fg};background:{bg};letter-spacing:0.02em'>{label}</span>"
    )

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

    # Keep only pairs that are relevant for roles available in this campaign.
    merged_map = dict(default_map)
    for source in (stored_map, session_map):
        for pair, form_id in source.items():
            if pair in default_map and form_id:
                merged_map[pair] = form_id

    for pair, form_id in default_map.items():
        if not merged_map.get(pair):
            merged_map[pair] = form_id

    st.session_state[map_key] = merged_map
    svc.upsert_role_form_defaults(campaign_id, merged_map)
    return map_key


def _resolve_campaign_name(campaign_id: int | None) -> str | None:
    if not campaign_id:
        return None
    campaign = svc.get_campaign(campaign_id)
    if not campaign:
        return f"Campaign #{campaign_id}"
    return _get(campaign, "name")


def _reset_campaign_page_view_state() -> None:
    if "create" in query_params:
        del query_params["create"]

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


def _navigate_campaign_breadcrumb(target: str, campaign_id: int | None = None) -> None:
    _reset_campaign_page_view_state()

    if target == "create":
        query_params["create"] = "true"
    elif target == "details" and campaign_id:
        st.session_state.show_view_dialog = True
        st.session_state.view_campaign_id = campaign_id

    st.rerun()


def _campaign_breadcrumb_segments():
    """Build breadcrumb segments from current Campaign page state."""
    segments = [
        {"label": "Home", "target": "list", "campaign_id": None, "current": False},
        {"label": "Campaigns", "target": "list", "campaign_id": None, "current": True},
    ]

    if query_params.get("create") == "true":
        segments[-1]["current"] = False
        segments.append({"label": "Create", "target": None, "campaign_id": None, "current": True})
        return segments

    if st.session_state.show_edit_dialog and st.session_state.edit_campaign_id:
        campaign_id = st.session_state.edit_campaign_id
        segments[-1]["current"] = False
        segments.append({"label": _resolve_campaign_name(campaign_id), "target": "details", "campaign_id": campaign_id, "current": False})
        segments.append({"label": "Edit", "target": None, "campaign_id": None, "current": True})
        return segments

    if st.session_state.show_view_dialog and st.session_state.view_campaign_id:
        campaign_id = st.session_state.view_campaign_id
        segments[-1]["current"] = False
        segments.append({"label": _resolve_campaign_name(campaign_id), "target": None, "campaign_id": None, "current": True})
        segments.append({"label": "Details", "target": None, "campaign_id": None, "current": True})
        return segments

    if st.session_state.show_team_assignment and st.session_state.team_campaign_id:
        campaign_id = st.session_state.team_campaign_id
        segments[-1]["current"] = False
        segments.append({"label": _resolve_campaign_name(campaign_id), "target": "details", "campaign_id": campaign_id, "current": False})
        segments.append({"label": "Team Assignment", "target": None, "campaign_id": None, "current": True})
        return segments

    if st.session_state.show_role_form_mapping and st.session_state.role_form_campaign_id:
        campaign_id = st.session_state.role_form_campaign_id
        segments[-1]["current"] = False
        segments.append({"label": _resolve_campaign_name(campaign_id), "target": "details", "campaign_id": campaign_id, "current": False})
        segments.append({"label": "Role Mapping", "target": None, "campaign_id": None, "current": True})
        return segments

    if (
        st.session_state.show_evaluation_matrix
        and st.session_state.matrix_campaign_id
        and st.session_state.matrix_group_id
    ):
        campaign_id = st.session_state.matrix_campaign_id
        segments[-1]["current"] = False
        segments.append({"label": _resolve_campaign_name(campaign_id), "target": "details", "campaign_id": campaign_id, "current": False})
        segments.append({"label": "Evaluation Matrix", "target": None, "campaign_id": None, "current": True})
        return segments

    if st.session_state.show_delete_confirm and st.session_state.delete_campaign_id:
        campaign_id = st.session_state.delete_campaign_id
        segments[-1]["current"] = False
        segments.append({"label": _resolve_campaign_name(campaign_id), "target": "details", "campaign_id": campaign_id, "current": False})
        segments.append({"label": "Delete", "target": None, "campaign_id": None, "current": True})
        return segments

    return segments


def _render_campaign_breadcrumbs():
    segments = [s for s in _campaign_breadcrumb_segments() if s and s.get("label")]
    if not segments:
        return

    if ui is None or not hasattr(ui, "breadcrumb"):
        with st.container(key="campaign_breadcrumbs_wrap"):
            cols = st.columns(len(segments) * 2 - 1)
            col_idx = 0

            for idx, seg in enumerate(segments):
                with cols[col_idx]:
                    is_current = idx == len(segments) - 1
                    if (not is_current) and seg.get("target"):
                        if st.button(seg["label"], key=f"campaign_crumb_{idx}", type="tertiary"):
                            _navigate_campaign_breadcrumb(seg["target"], seg.get("campaign_id"))
                    else:
                        st.markdown(
                            f"<span style='font-size:0.90rem;color:#0f172a;font-weight:600'>{seg['label']}</span>",
                            unsafe_allow_html=True,
                        )

                if idx < len(segments) - 1:
                    with cols[col_idx + 1]:
                        st.markdown("<span style='font-size:0.90rem;color:#94a3b8'>/</span>", unsafe_allow_html=True)

                col_idx += 2
        return

    breadcrumb_items = []
    for seg in segments:
        item = {"text": seg["label"], "isCurrentPage": bool(seg.get("current", False))}
        breadcrumb_items.append(item)

    clicked = ui.breadcrumb(
        breadcrumb_items=breadcrumb_items,
        class_name="text-sm mb-2",
        key="campaign_breadcrumb_shadcn",
    )

    if clicked:
        clicked_text = clicked.get("text") if isinstance(clicked, dict) else str(clicked)
        for seg in segments:
            if seg.get("label") == clicked_text and not seg.get("current") and seg.get("target"):
                _navigate_campaign_breadcrumb(seg["target"], seg.get("campaign_id"))
                break


# ----------------------------
# Page header
# ----------------------------
_render_campaign_breadcrumbs()
with st.container(border=True):
    header_left, header_right = st.columns([0.78, 0.22], vertical_alignment="center")
    with header_left:
        st.markdown(
            """
            <div style='margin-top:0.05rem;margin-bottom:0.1rem'>
              <div style='font-size:2.15rem;font-weight:800;color:#0f172a;line-height:1.1'>
                Campaign Management
              </div>
              <div style='font-size:1rem;color:#475569;margin-top:0.45rem'>
                Work surface for creating campaigns, tracking progress, and managing assignments.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with header_right:
        if query_params.get("create") != "true":
            st.write("")
            if st.button(f"{ICONS['add']} Create New Campaign", key="header_create_campaign_btn", type="primary", use_container_width=True):
                query_params["create"] = "true"
                st.rerun()

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
                    query_params.clear()
                    _campaign_flash_success_and_rerun(f"{ICONS['check']} Campaign '{name}' created successfully!")
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
                        st.session_state.show_edit_dialog = False
                        st.session_state.edit_campaign_id = None
                        _campaign_flash_success_and_rerun(f"{ICONS['check']} Campaign '{name}' updated successfully!")
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
            _counts = svc.get_campaign_counts(st.session_state.view_campaign_id)
            completed = int(_counts.get("completed", 0) or 0)
            total = int(_counts.get("total", 0) or 0)
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

        st.write("**Assigned Groups:**")
        if assigned_groups:
            for group in assigned_groups:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"{ICONS.get('office','🏢')} **{_get(group,'name')}**")
                with col2:
                    if st.button(
                        f"{ICONS['matrix']} Assignment Matrix",
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
        st.write("**Available Groups:**")
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
        role_names = _list_campaign_role_names(st.session_state.role_form_campaign_id)
        forms = svc.list_forms()

        if not forms:
            st.error(f"{ICONS['error']} No forms available. Please create an evaluation form first.")
        elif not role_names:
            st.error(
                f"{ICONS['error']} No campaign roles available yet. "
                "Assign groups to this campaign and make sure employees have organisation roles."
            )
        else:
            form_options = {f["name"]: f["id"] for f in forms}
            form_id_to_name = {f["id"]: f["name"] for f in forms}

            map_key = ensure_role_form_map(st.session_state.role_form_campaign_id, role_names, forms)

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
        st.caption("Rows = person being evaluated (evaluatee) • Columns = person giving evaluation (evaluator)")

        forms = svc.list_forms()
        role_names = _list_campaign_role_names(st.session_state.matrix_campaign_id)

        if not forms:
            st.error(f"{ICONS['error']} No forms available. Please create an evaluation form first.")
        elif not role_names:
            st.error(
                f"{ICONS['error']} No campaign roles available. "
                "Assign groups and roles before creating evaluations."
            )
        else:
            map_key = ensure_role_form_map(
                st.session_state.matrix_campaign_id,
                role_names,
                forms,
            )
            st.info("Forms are selected by evaluator role → evaluatee role defaults. Configure them from the campaign list.")
            st.write("---")

            st.write("**Manual Selection (Evaluator ↓ / Evaluatee →):**")
            st.caption("Check a cell when the COLUMN person should evaluate the ROW person.")

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
                    role_form_map = st.session_state.get(map_key, {}) if role_names and forms else {}

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
    campaigns = svc.list_campaigns()
    all_counts = svc.get_all_campaign_counts()

    if not campaigns:
        st.session_state.selected_campaign_id = None
        st.info(f"{ICONS.get('list','📋')} No campaigns found. Create your first campaign to get started!")
    else:
        rows = []
        for campaign in campaigns:
            campaign_id = _get(campaign, "id")
            _counts = all_counts.get(campaign_id, {"completed": 0, "total": 0})
            completed = int(_counts.get("completed", 0) or 0)
            total = int(_counts.get("total", 0) or 0)
            start_date = _to_date(_get(campaign, "start_date"))
            end_date = _to_date(_get(campaign, "end_date"))
            status = _campaign_status_meta(campaign, completed, total)
            deadline_label, deadline_color, remaining_seconds = _format_deadline(_get(campaign, "end_date"))

            rows.append(
                {
                    "campaign": campaign,
                    "id": campaign_id,
                    "name": _get(campaign, "name") or "Unnamed",
                    "description": (_get(campaign, "description") or "").lower(),
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": bool(_get(campaign, "is_active")),
                    "completed": completed,
                    "total": total,
                    "completion_pct": status["completion_pct"],
                    "status_label": status["label"],
                    "status_fg": status["fg"],
                    "status_bg": status["bg"],
                    "status_rank": status["rank"],
                    "deadline_label": deadline_label,
                    "deadline_color": deadline_color,
                    "remaining_seconds": remaining_seconds,
                }
            )

        with st.container(border=True):
            st.markdown("#### Filters")
            f1, f2 = st.columns([2.8, 1.2])
            with f1:
                search_text = st.text_input(
                    "Search by campaign name or description",
                    value="",
                    key="campaign_filter_search",
                    placeholder="Type campaign name...",
                ).strip().lower()
            with f2:
                sort_by = st.selectbox(
                    "Sort by",
                    options=["Status", "Name", "Start date", "End date", "Completion %", "Days left"],
                    key="campaign_filter_sort_by",
                )

            with st.expander("Advanced filters", expanded=False):
                st.caption("Open and tick only the statuses you want to see.")
                s1, s2, s3, s4 = st.columns(4)
                with s1:
                    status_active = st.checkbox("ACTIVE", value=True, key="campaign_filter_status_active")
                with s2:
                    status_pending_results = st.checkbox("PENDING RESULTS", value=True, key="campaign_filter_status_pending_results")
                with s3:
                    status_inactive = st.checkbox("INACTIVE", value=True, key="campaign_filter_status_inactive")
                with s4:
                    status_closed = st.checkbox("CLOSED", value=True, key="campaign_filter_status_closed")

                selected_statuses = []
                if status_active:
                    selected_statuses.append("ACTIVE")
                if status_pending_results:
                    selected_statuses.append("PENDING RESULTS")
                if status_inactive:
                    selected_statuses.append("INACTIVE")
                if status_closed:
                    selected_statuses.append("CLOSED")

                f5, = st.columns([1.2])
                with f5:
                    min_completion = st.slider(
                        "Min completion %",
                        min_value=0,
                        max_value=100,
                        value=0,
                        step=5,
                        key="campaign_filter_min_completion",
                    )

                f6, f7, f8, f9 = st.columns([1.2, 1.2, 1.2, 1.2])
                with f6:
                    start_from = st.date_input("Start from", value=None, key="campaign_filter_start_from")
                with f7:
                    start_to = st.date_input("Start to", value=None, key="campaign_filter_start_to")
                with f8:
                    end_from = st.date_input("End from", value=None, key="campaign_filter_end_from")
                with f9:
                    end_to = st.date_input("End to", value=None, key="campaign_filter_end_to")

            if "campaign_filter_min_completion" not in st.session_state:
                min_completion = 0
            else:
                min_completion = st.session_state.campaign_filter_min_completion

            start_from = st.session_state.get("campaign_filter_start_from")
            start_to = st.session_state.get("campaign_filter_start_to")
            end_from = st.session_state.get("campaign_filter_end_from")
            end_to = st.session_state.get("campaign_filter_end_to")

            selected_statuses = [
                status for status, enabled in [
                    ("ACTIVE", st.session_state.get("campaign_filter_status_active", True)),
                    ("PENDING RESULTS", st.session_state.get("campaign_filter_status_pending_results", True)),
                    ("INACTIVE", st.session_state.get("campaign_filter_status_inactive", True)),
                    ("CLOSED", st.session_state.get("campaign_filter_status_closed", True)),
                ]
                if enabled
            ]

        filtered_rows = rows
        if search_text:
            filtered_rows = [
                r
                for r in filtered_rows
                if search_text in r["name"].lower() or search_text in r["description"]
            ]

        if selected_statuses:
            filtered_rows = [r for r in filtered_rows if r["status_label"] in selected_statuses]

        filtered_rows = [r for r in filtered_rows if r["completion_pct"] >= float(min_completion)]

        if start_from:
            filtered_rows = [r for r in filtered_rows if r["start_date"] and r["start_date"] >= start_from]
        if start_to:
            filtered_rows = [r for r in filtered_rows if r["start_date"] and r["start_date"] <= start_to]
        if end_from:
            filtered_rows = [r for r in filtered_rows if r["end_date"] and r["end_date"] >= end_from]
        if end_to:
            filtered_rows = [r for r in filtered_rows if r["end_date"] and r["end_date"] <= end_to]

        sort_key_map = {
            "Status": lambda r: (r["status_rank"], r["name"].lower()),
            "Name": lambda r: r["name"].lower(),
            "Start date": lambda r: r["start_date"] or date.max,
            "End date": lambda r: r["end_date"] or date.max,
            "Completion %": lambda r: r["completion_pct"],
            "Days left": lambda r: (r["remaining_seconds"] if r["remaining_seconds"] is not None else 10**12),
        }
        filtered_rows = sorted(
            filtered_rows,
            key=sort_key_map.get(sort_by, sort_key_map["Status"]),
            reverse=(sort_by in {"Start date", "Completion %"}),
        )

        st.write("")
        st.subheader("Campaign List")
        st.caption(f"Showing {len(filtered_rows)} of {len(rows)} campaigns")

        visible_ids = {r["id"] for r in filtered_rows}
        if st.session_state.selected_campaign_id not in visible_ids:
            st.session_state.selected_campaign_id = None

        if not filtered_rows:
            st.info("No campaigns match the selected filters.")
            selected_campaign = None
        else:
            h1, h2, h3, h4, h5 = st.columns([4.2, 1.5, 2.0, 1.3, 0.7], vertical_alignment="center")
            with h1:
                st.caption("Campaign")
            with h2:
                st.caption("Status")
            with h3:
                st.caption("Completion")
            with h4:
                st.caption("Deadline")
            with h5:
                st.caption("Action")

            st.divider()

            for row in filtered_rows:
                c1, c2, c3, c4, c5 = st.columns([4.2, 1.5, 2.0, 1.3, 0.7], vertical_alignment="center")
                with c1:
                    start_str = row["start_date"].strftime("%Y-%m-%d") if row["start_date"] else "N/A"
                    end_str = row["end_date"].strftime("%Y-%m-%d") if row["end_date"] else "N/A"
                    st.markdown(f"**{row['name']}**")
                    st.caption(f"Start: {start_str} • End: {end_str}")
                with c2:
                    st.markdown(
                        _status_badge_html(row["status_label"], row["status_fg"], row["status_bg"]),
                        unsafe_allow_html=True,
                    )
                with c3:
                    if int(row["total"]) == 0:
                        st.markdown("**No evaluations yet**")
                        st.progress(0.0)
                    else:
                        st.markdown(f"**{row['completion_pct']:.0f}%** ({row['completed']}/{row['total']})")
                        st.progress(float(row["completion_pct"]) / 100)
                with c4:
                    st.markdown(
                        f"<span style='color:{row['deadline_color']};font-weight:700'>{row['deadline_label']}</span>",
                        unsafe_allow_html=True,
                    )
                with c5:
                    if st.button("→", key=f"open_{row['id']}", use_container_width=True):
                        st.session_state.selected_campaign_id = row["id"]
                        st.session_state.scroll_to_selected_campaign = True
                        st.rerun()

                st.divider()

            selected_campaign = next(
                (r["campaign"] for r in filtered_rows if r["id"] == st.session_state.selected_campaign_id),
                filtered_rows[0]["campaign"],
            )
            st.session_state.selected_campaign_id = _get(selected_campaign, "id")

        if selected_campaign:
            with st.container(key="selected_campaign_panel_anchor"):
                st.write("")

            st.markdown(
                """
                <style>
                div[class*="st-key-view_"] button,
                div[class*="st-key-results_"] button,
                div[class*="st-key-edit_"] button,
                div[class*="st-key-teams_"] button,
                div[class*="st-key-role_forms_"] button,
                div[class*="st-key-toggle_"] button,
                div[class*="st-key-delete_"] button {
                    min-height: 74px;
                    height: 74px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    white-space: normal;
                }
                div[class*="st-key-delete_"] button {
                    border-color: #ef4444;
                    color: #b91c1c;
                    background: #fff5f5;
                }
                div[class*="st-key-delete_"] button:hover {
                    background: #fee2e2;
                    border-color: #dc2626;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.get("scroll_to_selected_campaign"):
                if scroll_to_element is not None or _SCROLL_COMPONENT is not None:
                    _scroll_to_element_force("selected_campaign_panel_anchor")
                else:
                    st.markdown(
                        """
                        <script>
                        setTimeout(() => {
                            const target = window.parent.document.querySelector('.st-key-selected_campaign_panel_anchor');
                            if (target) {
                                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            }
                        }, 60);
                        </script>
                        """,
                        unsafe_allow_html=True,
                    )
                st.session_state.scroll_to_selected_campaign = False

            st.write("---")
            _counts = all_counts.get(_get(selected_campaign, "id"), {"completed": 0, "total": 0})
            completed = int(_counts.get("completed", 0) or 0)
            total = int(_counts.get("total", 0) or 0)
            status_meta = _campaign_status_meta(selected_campaign, completed, total)
            completion_pct = status_meta["completion_pct"]

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"### {_get(selected_campaign,'name')}")
                start_str = _get(selected_campaign, "start_date").strftime("%Y-%m-%d")
                end_dt = _get(selected_campaign, "end_date")
                end_str = end_dt.strftime("%Y-%m-%d") if end_dt else "N/A"
                st.caption(f"Start: {start_str} | End: {end_str}")
            with col2:
                st.write("")
                st.markdown(
                    _status_badge_html(status_meta["label"], status_meta["fg"], status_meta["bg"]),
                    unsafe_allow_html=True,
                )
            with col3:
                st.write("")
                if total == 0:
                    st.write("**No evaluations yet**")
                else:
                    st.write(f"**{completed}/{total}**")

            if total == 0:
                st.progress(0.0, text="Completion: No evaluations yet")
            else:
                st.progress(completion_pct / 100, text=f"Completion: {completion_pct:.0f}% ({completed}/{total})")

            selected_campaign_id = _get(selected_campaign, "id")
            selected_campaign_name = _get(selected_campaign, "name")

            # Step list between campaign header and action icons
            if steps_component is not None:
                step_labels = [
                    "Campaign setup",
                    "Assign groups",
                    "Assignment matrix",
                    "Assign role forms",
                    "Collect Responses",
                    "Review results",
                    "Close campaign",
                ]
                step_tooltips = [
                    "Campaign alapadatok és időszak beállítása.",
                    "Csoportok hozzárendelése a kampányhoz.",
                    "Ki kit értékeljen: értékelési mátrix feltöltése.",
                    "Szerepkörökhöz alapértelmezett űrlapok hozzárendelése.",
                    "A kitöltött értékelések beérkezése.",
                    "Eredmények és statisztikák áttekintése.",
                    "Kampány lezárása.",
                ]

                assigned_groups = svc.list_campaign_groups(selected_campaign_id)
                has_groups = bool(assigned_groups)
                role_defaults = svc.get_role_form_defaults(selected_campaign_id) if has_groups else {}
                has_role_defaults = any(v is not None for v in role_defaults.values()) if role_defaults else False
                has_generated_evaluations = total > 0
                has_any_completion = completed > 0
                has_closed_campaign = status_meta["label"] == "CLOSED"

                current_step = 0
                if has_groups:
                    current_step = 1
                if has_generated_evaluations:
                    current_step = 2
                if has_role_defaults:
                    current_step = 3
                if has_any_completion:
                    current_step = 4
                if has_generated_evaluations and completed == total and total > 0:
                    current_step = 5
                if has_closed_campaign:
                    current_step = 6

                steps_component(
                    labels=step_labels,
                    icons=[1, 2, 3, 4, 5, 6, 7],
                    current=current_step,
                    horizontal=True,
                    key=f"campaign_steps_{selected_campaign_id}",
                )

                st.markdown(
                    """
                    <script>
                    setTimeout(() => {
                        const labels = [
                            "Campaign setup",
                            "Assign groups",
                            "Assignment matrix",
                            "Assign role forms",
                            "Collect Responses",
                            "Review results",
                            "Close campaign",
                        ];
                        const tips = [
                            "Campaign alapadatok és időszak beállítása.",
                            "Csoportok hozzárendelése a kampányhoz.",
                            "Ki kit értékeljen: értékelési mátrix feltöltése.",
                            "Szerepkörökhöz alapértelmezett űrlapok hozzárendelése.",
                            "A kitöltött értékelések beérkezése.",
                            "Eredmények és statisztikák áttekintése.",
                            "Kampány lezárása.",
                        ];

                        const root = window.parent.document;
                        labels.forEach((label, idx) => {
                            const nodes = root.querySelectorAll('span, div, p');
                            nodes.forEach((n) => {
                                if ((n.textContent || '').trim() === label) {
                                    n.setAttribute('title', tips[idx]);
                                    n.style.cursor = 'help';
                                }
                            });
                        });
                    }, 120);
                    </script>
                    """,
                    unsafe_allow_html=True,
                )
                st.write("")

            col_view, col_results, col_edit, col_teams, col_role_forms, col_toggle, col_spacer, col_delete = st.columns([1, 1, 1, 1, 1, 1, 0.2, 1])

            with col_view:
                if st.button(
                    f"{ICONS['view']} View",
                    key=f"view_{selected_campaign_id}",
                    use_container_width=True,
                    help="Open campaign details",
                ):
                    st.session_state.show_view_dialog = True
                    st.session_state.view_campaign_id = selected_campaign_id
                    st.rerun()

            with col_results:
                if st.button(
                    ":material/assessment: View Results",
                    key=f"results_{selected_campaign_id}",
                    use_container_width=True,
                    help="Open campaign analytics and results",
                ):
                    st.session_state.cr_view = "campaign"
                    st.session_state.cr_selected_campaign_id = selected_campaign_id
                    st.session_state.cr_selected_campaign_name = selected_campaign_name
                    st.session_state.cr_selected_employee_id = None
                    st.session_state.cr_selected_employee_name = None
                    st.switch_page("ui/pages/results/campaign_results_page.py")

            with col_edit:
                if _get(selected_campaign, "is_active"):
                    if st.button(
                        f"{ICONS['edit']} Edit",
                        key=f"edit_{selected_campaign_id}",
                        use_container_width=True,
                        help="Edit campaign details",
                    ):
                        st.session_state.show_edit_dialog = True
                        st.session_state.edit_campaign_id = selected_campaign_id
                        st.rerun()
                else:
                    st.button(
                        f"{ICONS['edit']} Edit",
                        key=f"edit_{selected_campaign_id}",
                        disabled=True,
                        use_container_width=True,
                        help="Inactive campaigns cannot be edited",
                    )

            with col_teams:
                if st.button(
                    f"{ICONS['teams']} Groups",
                    key=f"teams_{selected_campaign_id}",
                    use_container_width=True,
                    help="Assign teams and manage matrix",
                ):
                    forms = svc.list_forms()
                    role_names = _list_campaign_role_names(selected_campaign_id)
                    if role_names and forms:
                        ensure_role_form_map(selected_campaign_id, role_names, forms)
                    st.session_state.show_team_assignment = True
                    st.session_state.team_campaign_id = selected_campaign_id
                    st.rerun()

            with col_role_forms:
                if st.button(
                    f"{ICONS['matrix']} Assign forms",
                    key=f"role_forms_{selected_campaign_id}",
                    use_container_width=True,
                    help="Configure role-to-form defaults",
                ):
                    st.session_state.show_role_form_mapping = True
                    st.session_state.role_form_campaign_id = selected_campaign_id
                    st.rerun()

            with col_toggle:
                toggle_icon = ICONS["pause"] if _get(selected_campaign, "is_active") else ICONS["play"]
                toggle_label = (
                    f"{toggle_icon} Pause" if _get(selected_campaign, "is_active") else f"{toggle_icon} Activate"
                )
                if st.button(
                    toggle_label,
                    key=f"toggle_{selected_campaign_id}",
                    use_container_width=True,
                    help="Pause or activate campaign",
                ):
                    try:
                        svc.toggle_campaign(selected_campaign_id)
                        st.rerun()
                    except Exception as e:
                        st.error(f"{ICONS['error']} Toggle failed: {e}")

            with col_spacer:
                st.write("")

            with col_delete:
                if st.button(
                    f"{ICONS['delete']} Delete",
                    key=f"delete_{selected_campaign_id}",
                    use_container_width=True,
                    help="Delete campaign permanently",
                ):
                    st.session_state.show_delete_confirm = True
                    st.session_state.delete_campaign_id = selected_campaign_id
                    st.rerun()

        else:
            st.info("Choose a campaign card above to manage it.")

st.write("")
st.info(f"{ICONS['lightbulb']} **Tip:** Use the Teams button to assign groups and configure evaluation matrices for each campaign.")
