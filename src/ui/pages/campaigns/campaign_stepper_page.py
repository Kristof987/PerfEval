from __future__ import annotations

import streamlit as st

from services.campaign_service import CampaignService
from ui.pages.campaigns.common.consts import PHASES
from ui.pages.campaigns.common.consts import PHASE_SHORT
from ui.pages.campaigns.common.styles import append_background_and_colour_stepper_style, append_active_step_highlight
from ui.pages.campaigns.helpers.helpers import datetime_to_string, count_days_left, date_to_datetime, get
from ui.pages.campaigns.render_stepper_closure_content import render_closure
from ui.pages.campaigns.render_stepper_evaluate_content import render_evaluation
from ui.pages.campaigns.render_stepper_forms_content import render_forms
from ui.pages.campaigns.render_stepper_results_content import render_results
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

    append_background_and_colour_stepper_style(css_rules, completed_until)
    append_active_step_highlight(css_rules, current)

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
        render_evaluation(selected_id)
    elif phase_index == 5:
        render_results(selected_id, campaign_name)
    else:
        render_closure(selected_id)

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
