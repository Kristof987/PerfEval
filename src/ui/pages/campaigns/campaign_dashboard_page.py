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


def _stepper(current: int, meta_right: str = "") -> None:
    pct = int((current / max(len(PHASES) - 1, 1)) * 100)
    crumbs: list[str] = []
    for i, label in enumerate(PHASE_SHORT):
        if i < current:
            crumbs.append(f'<span style="color:#1D9E75">{label}</span>')
        elif i == current:
            crumbs.append(f'<span style="color:#2a2a2a;font-weight:600">{label}</span>')
        else:
            crumbs.append(f'<span style="color:#aaa">{label}</span>')

    breadcrumb = ' <span style="color:#ccc;margin:0 2px">›</span> '.join(crumbs)
    meta = f'<span style="font-size:13px;color:#888;white-space:nowrap">{meta_right}</span>' if meta_right else ""
    st.markdown(
        f"""
        <div style="padding:10px 16px;background:#f8f8f6;border-radius:10px;border:1px solid #eee;margin-bottom:1rem;
            font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;font-size:13px;color:#333;gap:8px">
                <div style="overflow-x:auto;white-space:nowrap">{breadcrumb}</div>{meta}
            </div>
            <div style="height:4px;background:#e5e5e0;border-radius:2px;overflow:hidden">
                <div style="height:100%;width:{pct}%;border-radius:2px;background:linear-gradient(90deg,#1D9E75,#185FA5)"></div>
            </div>
        </div>
        """,
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

active_items = [c for c in campaigns if bool(getattr(c, "is_active", False))]
inactive_items = [c for c in campaigns if not bool(getattr(c, "is_active", False))]

if active_items:
    st.markdown(
        "<p style='font-size:12px;font-weight:500;color:#888;text-transform:uppercase;"
        "letter-spacing:.4px;margin-bottom:4px'>Active campaigns</p>",
        unsafe_allow_html=True,
    )

for campaign in active_items:
    campaign_id = int(getattr(campaign, "id", 0) or 0)
    name = getattr(campaign, "name", "Untitled campaign")
    description = getattr(campaign, "description", None)
    comment = getattr(campaign, "comment", None)
    start_date = getattr(campaign, "start_date", None)
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
            st.markdown(_active_badge(), unsafe_allow_html=True)

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

        if not_started > 0:
            st.warning(f"**{not_started} employees** have not started yet.", icon="⚠️")

        c_open, c_edit = st.columns([1, 1])
        with c_open:
            if st.button("Continue →", type="primary", key=f"open_active_{campaign_id}"):
                st.session_state.campaign_dashboard_selected_id = campaign_id
                st.switch_page("pages/campaign_stepper_page.py")

        if comment:
            st.caption(f"Comment: {comment}")

if inactive_items:
    st.write("")
    st.markdown(
        "<p style='font-size:12px;font-weight:500;color:#888;text-transform:uppercase;"
        "letter-spacing:.4px;margin-bottom:4px'>Previous campaigns</p>",
        unsafe_allow_html=True,
    )

for campaign in inactive_items:
    campaign_id = int(getattr(campaign, "id", 0) or 0)
    name = getattr(campaign, "name", "Untitled campaign")
    end_date = getattr(campaign, "end_date", None)
    participants = int(all_counts.get(campaign_id, {"total": 0}).get("total", 0) or 0)

    with st.container(border=True):
        r1, r2 = st.columns([5, 1])
        with r1:
            st.subheader(name)
            st.caption(f"Closed: {_fmt_dt(end_date)} · {participants} participants")
        with r2:
            st.button("View", key=f"open_prev_{campaign_id}")

st.markdown("")
if st.button("+ Create new campaign", key="new_campaign_placeholder"):
    st.session_state.campaign_dashboard_selected_id = "new"
    st.switch_page("pages/campaign_stepper_page.py")

