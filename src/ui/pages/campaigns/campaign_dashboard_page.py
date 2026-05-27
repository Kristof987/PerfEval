from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.common.consts import PHASES
from ui.pages.campaigns.helpers.helpers import datetime_to_string, to_date, count_days_left


def _icon(key: str, fallback: str = "") -> str:
    return ICONS.get(key, fallback)

def _get(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def _active_badge() -> str:
    return (
        "<span style='background:#e6f1fb;color:#0c447c;padding:4px 12px;"
        "border-radius:20px;font-size:12px;font-weight:500'>Active</span>"
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
        return PHASES[0]

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
        return PHASES[next_step_index]
    except Exception:
        completed_by_id = st.session_state.get("campaign_dashboard_completed_phase_by_id", {})
        completed_phase = int(completed_by_id.get(str(campaign_id), -1))
        next_step_index = min(len(PHASES) - 1, max(0, completed_phase + 1))
        return PHASES[next_step_index]

all_counts = {}
try:
    all_counts = svc.get_all_campaign_counts()
except Exception:
    all_counts = {}

def _campaign_status_meta(campaign, completed: int, total: int) -> dict:
    today = date.today()
    end_date = to_date(_get(campaign, "end_date"))
    is_active = bool(_get(campaign, "is_active", False))
    comment = str(_get(campaign, "comment") or "")
    is_pending_results = "[PENDING_RESULTS]" in comment
    is_closed_marked = "[CLOSED]" in comment
    completion_pct = (completed / total * 100) if total > 0 else 0

    if is_closed_marked and not is_active:
        return {"label": "CLOSED", "fg": "#991b1b", "bg": "#fee2e2", "section": "CLOSED"}
    if ((end_date is not None and end_date < today) or completion_pct >= 100) and not is_active:
        return {"label": "CLOSED", "fg": "#991b1b", "bg": "#fee2e2", "section": "CLOSED"}
    if is_pending_results:
        return {"label": "PENDING RESULTS", "fg": "#7c2d12", "bg": "#ffedd5", "section": "PENDING RESULTS"}
    if is_active:
        return {"label": "ACTIVE", "fg": "#065f46", "bg": "#dcfce7", "section": "ACTIVE"}
    return {"label": "INACTIVE", "fg": "#334155", "bg": "#e2e8f0", "section": "INACTIVE"}


def _status_badge_html(label: str, fg: str, bg: str, compact: bool = False) -> str:
    padding = "2px 8px" if compact else "4px 12px"
    font_size = "10px" if compact else "12px"
    font_weight = "500" if compact else "600"
    return (
        f"<span style='background:{bg};color:{fg};padding:{padding};"
        f"border-radius:20px;font-size:{font_size};font-weight:{font_weight}'>{label}</span>"
    )


rows = []
for campaign in campaigns:
    campaign_id = int(getattr(campaign, "id", 0) or 0)
    counts = all_counts.get(campaign_id, {"completed": 0, "total": 0})
    done = int(counts.get("completed", 0) or 0)
    participants = int(counts.get("total", 0) or 0)
    meta = _campaign_status_meta(campaign, done, participants)
    rows.append((campaign, meta))

sections = [
    ("ACTIVE", "Active campaigns"),
    ("PENDING RESULTS", "Pending results"),
    ("INACTIVE", "Inactive campaigns"),
    ("CLOSED", "Closed campaigns"),
]

for section_key, section_title in sections:
    section_items = [(c, m) for c, m in rows if m["section"] == section_key]
    if not section_items:
        continue

    is_large_section = section_key in ("ACTIVE", "PENDING RESULTS")

    st.markdown(
        f"<p style='font-size:12px;font-weight:500;color:#888;text-transform:uppercase;"
        f"letter-spacing:.4px;margin-bottom:4px'>{section_title}</p>",
        unsafe_allow_html=True,
    )

    for campaign, status_meta in section_items:
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
        deadline_text = datetime_to_string(end_date)
        days_left = count_days_left(end_date)

        with st.container(border=True):
            top_left, top_right = st.columns([5, 1])
            with top_left:
                title_md = f"**{name}**" if is_large_section else f"<span style='font-size:0.9rem;font-weight:600'>{name}</span>"
                st.markdown(title_md, unsafe_allow_html=not is_large_section)
                if is_large_section:
                    st.caption(f"{description or 'No description'} · {participants} participants")
                else:
                    st.markdown(
                        f"<p style='margin:0;color:#6b7280;font-size:12px'>{participants} participants</p>",
                        unsafe_allow_html=True,
                    )
            with top_right:
                st.markdown(
                    _status_badge_html(
                        status_meta["label"],
                        status_meta["fg"],
                        status_meta["bg"],
                        compact=not is_large_section,
                    ),
                    unsafe_allow_html=True,
                )

            if is_large_section:
                p1, p2 = st.columns([4, 2])
                with p1:
                    st.caption(f"**Progress** — {pct}% complete")
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
                m4.metric("Next Step", _step_label_for_campaign(campaign))
            else:
                st.markdown(
                    f"<p style='margin:0;color:#6b7280;font-size:12px'>"
                    f"Progress: {pct}% · Next Step: {_step_label_for_campaign(campaign)} · Deadline: {deadline_text}"
                    f"</p>",
                    unsafe_allow_html=True,
                )

            c_open, _ = st.columns([1, 1])
            with c_open:
                action_label = "Continue →" if status_meta["label"] in ("ACTIVE", "PENDING RESULTS") else "Open →"
                if st.button(action_label, type="primary", key=f"open_{status_meta['section']}_{campaign_id}"):
                    st.session_state.campaign_dashboard_selected_id = campaign_id
                    st.switch_page("ui/pages/campaigns/campaign_stepper_page.py")

st.markdown("")
if st.button("+ Create new campaign", key="new_campaign_placeholder"):
    st.session_state.campaign_dashboard_selected_id = "new"
    st.switch_page("ui/pages/campaigns/campaign_stepper_page.py")

