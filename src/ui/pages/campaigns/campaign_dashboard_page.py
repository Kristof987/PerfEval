from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService


PHASES = [
    "Campaign creation",
    "Team selection",
    "Form assignments",
    "Evaluation matrix",
    "Evaluate",
    "Results",
    "Closure",
]

PHASE_SHORT = [
    "Campaign Setup",
    "Groups",
    "Forms",
    "Assignment Matrix",
    "Evaluate",
    "Results",
    "Close",
]


def _icon(key: str, fallback: str = "") -> str:
    return ICONS.get(key, fallback)


def _get(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


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


def _active_badge() -> str:
    return (
        "<span style='background:#e6f1fb;color:#0c447c;padding:4px 12px;"
        "border-radius:20px;font-size:12px;font-weight:500'>Active</span>"
    )


def _status_badge(label: str) -> str:
    if label == "ACTIVE":
        return (
            "<span style='background:#e6f1fb;color:#0c447c;padding:4px 12px;"
            "border-radius:20px;font-size:12px;font-weight:500'>Active</span>"
        )
    if label == "PENDING RESULTS":
        return (
            "<span style='background:#ffedd5;color:#7c2d12;padding:4px 12px;"
            "border-radius:20px;font-size:12px;font-weight:500'>Pending results</span>"
        )
    if label == "CLOSED":
        return (
            "<span style='background:#fee2e2;color:#991b1b;padding:4px 12px;"
            "border-radius:20px;font-size:12px;font-weight:500'>Closed</span>"
        )
    return (
        "<span style='background:#e2e8f0;color:#334155;padding:4px 12px;"
        "border-radius:20px;font-size:12px;font-weight:500'>Inactive</span>"
    )


def _campaign_status_label(campaign) -> str:
    today = date.today()
    end_date = _to_date(_get(campaign, "end_date"))
    is_active = bool(_get(campaign, "is_active", False))
    comment = str(_get(campaign, "comment") or "")

    if end_date and end_date < today:
        return "CLOSED"
    if "[PENDING_RESULTS]" in comment:
        return "PENDING RESULTS"
    if is_active:
        return "ACTIVE"
    return "INACTIVE"


def _stepper(current: int, meta_right: str = "") -> None:
    n = len(PHASES)
    pct = int((current / max(n - 1, 1)) * 100)

    css_rules = []
    for i in range(max(0, current)):
        css_rules.append(
            f"div[role='radiogroup'] > button:nth-child({i + 1}) {{"
            f"  background-color: #10B981 !important;"
            f"  color: #fff !important;"
            f"  border-color: #10B981 !important;"
            f"}}"
        )
    css_rules.append(
        f"div[role='radiogroup'] > button:nth-child({current + 1}) {{"
        f"  box-shadow: inset 0 0 0 2px rgba(255,255,255,0.88), 0 0 0 3px rgba(16, 185, 129, 0.35), 0 0 0 5px rgba(16, 185, 129, 0.16) !important;"
        f"  border-color: #10B981 !important;"
        f"  transform: translateY(-1px);"
        f"}}"
    )

    st.markdown(f"<style>\n{chr(10).join(css_rules)}\n</style>", unsafe_allow_html=True)

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

    st.pills(
        "dashboard_campaign_step",
        options=list(range(n)),
        format_func=lambda i: PHASE_SHORT[i],
        default=current,
        label_visibility="collapsed",
        key=f"dashboard_stepper_{current}",
    )

    st.markdown(
        f"""<div style="height:4px;background:#e5e5e0;border-radius:2px;overflow:hidden;margin-top:-0.5rem;margin-bottom:0.35rem">
            <div style="height:100%;width:{pct}%;border-radius:2px;background:linear-gradient(90deg,#10B981,#185FA5)"></div>
        </div>""",
        unsafe_allow_html=True,
    )


st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
        /* No page zoom: only make component sizes smaller */
        html, body, [class*="css"] {
            font-size: 14px;
        }

        h1, h2, h3 {
            font-size: 0.92em;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 0.78rem;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.15rem;
        }

        .stButton > button {
            font-size: 0.82rem;
            padding-top: 0.28rem;
            padding-bottom: 0.28rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Evaluation Campaigns")
st.caption("Manage performance evaluation cycles")

svc = CampaignService()

try:
    campaigns = svc.list_campaigns()
except Exception as exc:
    st.error(f"{_icon('error', ':material/error:')} Could not load campaigns: {exc}")
    st.stop()

if not campaigns:
    st.info(f"{_icon('info', ':material/info:')} No campaigns found.")
    st.stop()

if "campaign_dashboard_selected_id" not in st.session_state:
    st.session_state.campaign_dashboard_selected_id = None
if "campaign_dashboard_phase_by_id" not in st.session_state:
    st.session_state.campaign_dashboard_phase_by_id = {}
if "campaign_dashboard_completed_phase_by_id" not in st.session_state:
    st.session_state.campaign_dashboard_completed_phase_by_id = {}
if "campaign_dashboard_teams_invalidated_by_id" not in st.session_state:
    st.session_state.campaign_dashboard_teams_invalidated_by_id = {}


def _step_label_for_campaign(campaign) -> str:
    campaign_id = int(_get(campaign, "id", 0) or 0)
    if campaign_id <= 0:
        return f"1 / {len(PHASES)}"

    try:
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

        has_closed_campaign = not bool(_get(campaign, "is_active", True))

        completed_phase = 0
        if has_groups:
            completed_phase = 1
        if has_role_defaults:
            completed_phase = 2
        if has_full_matrix_coverage:
            completed_phase = 3
        if has_any_completion:
            completed_phase = 5
        if has_closed_campaign:
            completed_phase = 6

        invalidated_by_id = st.session_state.get("campaign_dashboard_teams_invalidated_by_id", {})
        if bool(invalidated_by_id.get(str(campaign_id), False)):
            completed_phase = min(completed_phase, 1)

        completed_by_id = st.session_state.get("campaign_dashboard_completed_phase_by_id", {})
        completed_by_id[str(campaign_id)] = completed_phase
        st.session_state.campaign_dashboard_completed_phase_by_id = completed_by_id

        next_step_index = min(len(PHASES) - 1, max(0, completed_phase + 1))
        return f"{next_step_index + 1} / {len(PHASES)}"
    except Exception:
        completed_by_id = st.session_state.get("campaign_dashboard_completed_phase_by_id", {})
        completed_phase = int(completed_by_id.get(str(campaign_id), -1))
        next_step_index = min(len(PHASES) - 1, max(0, completed_phase + 1))
        return f"{next_step_index + 1} / {len(PHASES)}"

all_counts = {}
try:
    all_counts = svc.get_all_campaign_counts()
except Exception:
    all_counts = {}

active_items = [c for c in campaigns if _campaign_status_label(c) == "ACTIVE"]
pending_items = [c for c in campaigns if _campaign_status_label(c) == "PENDING RESULTS"]
closed_items = [c for c in campaigns if _campaign_status_label(c) == "CLOSED"]
inactive_items = [c for c in campaigns if _campaign_status_label(c) == "INACTIVE"]


def _render_campaign_list_item(campaign, status_label: str, section_key: str) -> None:
    campaign_id = int(getattr(campaign, "id", 0) or 0)
    name = getattr(campaign, "name", "Untitled campaign")
    description = getattr(campaign, "description", None)
    comment = getattr(campaign, "comment", None)
    end_date = getattr(campaign, "end_date", None)

    counts = all_counts.get(campaign_id, {"completed": 0, "total": 0})
    done = int(counts.get("completed", 0) or 0)
    participants = int(counts.get("total", 0) or 0)
    not_started = max(participants - done, 0)
    wip = 0
    pct = int((done / participants) * 100) if participants > 0 else 0
    deadline_text = _fmt_dt(end_date)
    days_left = _days_left(end_date)

    with st.container(border=True):
        top_left, top_right = st.columns([5, 1])
        with top_left:
            st.markdown(f"**{name}**")
            st.caption(f"{description or 'No description'} · {participants} participants")
        with top_right:
            st.markdown(_status_badge(status_label), unsafe_allow_html=True)

        p1, p2 = st.columns([4, 2])
        with p1:
            st.caption(f"**Evaluation in progress** — {pct}% complete")
            st.progress(pct / 100)
        with p2:
            if days_left is None:
                st.caption(f"Deadline: {deadline_text}")
            else:
                st.caption(f"Deadline: {deadline_text} ({days_left} days)")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Completed", done)
        m2.metric("In progress", wip)
        m3.metric("Not started", not_started)
        m4.metric("Step", _step_label_for_campaign(campaign))

        if not_started > 0 and status_label in ("ACTIVE", "PENDING RESULTS"):
            st.warning(f"**{not_started} employees** have not started yet.", icon="⚠️")

        c_open, _ = st.columns([1, 1])
        with c_open:
            btn_label = "Continue →" if status_label in ("ACTIVE", "PENDING RESULTS") else "Open →"
            btn_type = "primary" if status_label in ("ACTIVE", "PENDING RESULTS") else "secondary"
            if st.button(btn_label, type=btn_type, key=f"open_{section_key}_{campaign_id}"):
                st.session_state.campaign_dashboard_selected_id = campaign_id
                st.switch_page("pages/campaign_stepper_page.py")

        if comment:
            st.caption(f"Comment: {comment}")

if active_items:
    st.markdown(
        "<p style='font-size:12px;font-weight:500;color:#888;text-transform:uppercase;"
        "letter-spacing:.4px;margin-bottom:4px'>Active campaigns</p>",
        unsafe_allow_html=True,
    )

for campaign in active_items:
    _render_campaign_list_item(campaign, "ACTIVE", "active")

if pending_items:
    st.write("")
    st.markdown(
        "<p style='font-size:12px;font-weight:500;color:#888;text-transform:uppercase;"
        "letter-spacing:.4px;margin-bottom:4px'>Pending results</p>",
        unsafe_allow_html=True,
    )

for campaign in pending_items:
    _render_campaign_list_item(campaign, "PENDING RESULTS", "pending")

if closed_items:
    st.write("")
    st.markdown(
        "<p style='font-size:12px;font-weight:500;color:#888;text-transform:uppercase;"
        "letter-spacing:.4px;margin-bottom:4px'>Closed campaigns</p>",
        unsafe_allow_html=True,
    )

for campaign in closed_items:
    _render_campaign_list_item(campaign, "CLOSED", "closed")

if inactive_items:
    st.write("")
    st.markdown(
        "<p style='font-size:12px;font-weight:500;color:#888;text-transform:uppercase;"
        "letter-spacing:.4px;margin-bottom:4px'>Inactive campaigns</p>",
        unsafe_allow_html=True,
    )

for campaign in inactive_items:
    _render_campaign_list_item(campaign, "INACTIVE", "inactive")

st.markdown("")
if st.button("+ Create new campaign", key="new_campaign_placeholder"):
    st.session_state.campaign_dashboard_selected_id = "new"
    st.switch_page("pages/campaign_stepper_page.py")

