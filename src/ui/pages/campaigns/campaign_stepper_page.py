from __future__ import annotations

import random
import runpy

import pandas as pd
import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.common.common import set_step_progress, cleanup_on_group_removal, invalidate_after_team_change
from ui.pages.campaigns.common.consts import PHASES
from ui.pages.campaigns.common.consts import PHASE_SHORT
from ui.pages.campaigns.helpers.helpers import datetime_to_string, count_days_left, date_to_datetime, get
from ui.pages.campaigns.render_stepper_forms_content import render_forms
from ui.pages.campaigns.render_stepper_reviewers_content import render_reviewers
from ui.pages.campaigns.render_stepper_setup_content import render_setup
from ui.pages.campaigns.render_stepper_groups_content import render_groups


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

def _infer_completed_phase(campaign_obj) -> int:
    campaign_id = int(get(campaign_obj, "id", 0) or 0)
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
                gid = int(get(group, "id", 0) or 0)
                if gid <= 0:
                    has_full_matrix_coverage = False
                    break
                matrix = svc.get_campaign_group_evaluations(campaign_id, gid)
                has_any_assignment = any(bool(evaluatees) for evaluatees in matrix.values())
                if not has_any_assignment:
                    has_full_matrix_coverage = False
                    break

        evaluations = svc.list_campaign_evaluations(campaign_id)
        has_any_completion = any(str(get(e, "status", "")).lower() == "completed" for e in evaluations)

        role_defaults = svc.get_role_form_defaults(campaign_id) if has_groups else {}
        has_role_defaults = any(v is not None for v in role_defaults.values()) if role_defaults else False

        has_closed_campaign = not bool(get(campaign_obj, "is_active", True))
        comment = str(get(campaign_obj, "comment") or "")
        is_closed_marked = "[CLOSED]" in comment

        completed_phase = 0
        if has_groups:
            completed_phase = 1
        if has_role_defaults:
            completed_phase = 2
        if has_full_matrix_coverage:
            completed_phase = 3
        if has_any_completion:
            completed_phase = 4
        if has_closed_campaign and is_closed_marked:
            completed_phase = 6

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
        render_setup(phase_index, selected_id, selected_campaign)
    elif phase_index == 1:
        render_groups(selected_id)
    elif phase_index == 2:
        render_forms(selected_id)
    elif phase_index == 3:
        render_reviewers(selected_id)
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
            evaluator_name = str(get(row, "evaluator_name", "Unknown"))
            status = str(get(row, "status", "")).lower()

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

        if campaign and bool(get(campaign, "is_active", True)):
            if st.button("Close Form Filling", type="primary", key="stepper_close_filling"):
                try:
                    close_fn = getattr(svc, "close_filling_period", None)
                    if callable(close_fn):
                        close_fn(campaign_id)
                    else:
                        # Backward-compatible fallback if old service instance is loaded
                        with svc.db.transaction() as conn:
                            svc.campaigns.close_filling_period(conn, campaign_id)
                    set_step_progress(selected_id, completed_phase=4, current_phase=5)
                    st.success("Filling period closed.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"{ICONS['error']} Could not close filling period: {exc}")
        else:
            set_step_progress(selected_id, current_phase=5)
            st.rerun()

    elif phase_index == 5:
        if selected_id == "new":
            st.warning("Create the campaign first, then open results.")
            return

        st.info(
            "Review campaign results here. Use the embedded results view to inspect participants, "
            "completion, and aggregated outcomes before final closure."
        )

        # Keep Results marked completed, but do not hard-force current_phase to 5,
        # so the top stepper remains freely clickable to earlier steps.
        set_step_progress(selected_id, completed_phase=5)
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
        if selected_id == "new":
            st.warning("Create the campaign first, then close it when the flow is finished.")
            return

        svc = CampaignService()
        campaign_id = int(selected_id)
        campaign = svc.get_campaign(campaign_id)
        if campaign is None:
            st.error("Campaign data is not available.")
            return

        comment = str(get(campaign, "comment") or "")
        # Consider campaign closed only when the explicit CLOSED marker is present.
        # This prevents "already closed" from appearing after filling is closed
        # (which sets is_active=False with [PENDING_RESULTS]).
        is_closed = "[CLOSED]" in comment

        st.caption("Finalize the campaign and lock it as closed.")

        if is_closed:
            set_step_progress(selected_id, completed_phase=6, current_phase=6, force_completed=True)
            st.success("Campaign is already closed.")
            return

        if st.button("Close Campaign", type="primary", key=f"stepper_close_campaign_{campaign_id}"):
            try:
                close_campaign_fn = getattr(svc, "close_campaign", None)
                if callable(close_campaign_fn):
                    close_campaign_fn(campaign_id)
                else:
                    with svc.db.transaction() as conn:
                        svc.campaigns.close_campaign(conn, campaign_id)

                set_step_progress(selected_id, completed_phase=6, current_phase=6, force_completed=True)
                st.success("Campaign closed.")
                st.rerun()
            except Exception as exc:
                st.error(f"{ICONS['error']} Could not close campaign: {exc}")


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
    selected_deadline = datetime_to_string(selected_end_date)
    selected_days_left = count_days_left(selected_end_date)
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
