import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.dashboard.dashboard_state import select_campaign_and_open
from ui.pages.campaigns.dashboard.dashboard_status import campaign_status_meta, get_value, step_label_for_campaign
from ui.pages.campaigns.dashboard.dashboard_styles import (
    compact_campaign_meta_html,
    compact_campaign_title_html,
    section_title_html,
    status_badge_html,
)
from ui.pages.campaigns.helpers.helpers import count_days_left, datetime_to_string


DASHBOARD_SECTIONS = [
    ("ACTIVE", "Active campaigns"),
    ("PENDING RESULTS", "Pending results"),
    ("INACTIVE", "Inactive campaigns"),
    ("CLOSED", "Closed campaigns"),
]


def icon(key: str, fallback: str = "") -> str:
    return ICONS.get(key, fallback)


def load_campaigns_or_stop(service: CampaignService):
    try:
        return service.list_campaigns()
    except Exception as exc:
        st.error(f"{icon('error', ':material/error:')} Could not load campaigns: {exc}")
        st.stop()


def load_all_campaign_counts(service: CampaignService) -> dict:
    try:
        return service.get_all_campaign_counts()
    except Exception:
        return {}


def build_campaign_dashboard_rows(campaigns, all_counts: dict) -> list[tuple[object, dict]]:
    rows = []
    for campaign in campaigns:
        campaign_id = int(getattr(campaign, "id", 0) or 0)
        counts = all_counts.get(campaign_id, {"completed": 0, "total": 0})
        done = int(counts.get("completed", 0) or 0)
        participants = int(counts.get("total", 0) or 0)
        rows.append((campaign, campaign_status_meta(campaign, done, participants)))
    return rows


def render_campaign_card(service: CampaignService, campaign, status_meta: dict, all_counts: dict, is_large_section: bool) -> None:
    campaign_id = int(getattr(campaign, "id", 0) or 0)
    name = getattr(campaign, "name", "Untitled campaign")
    description = getattr(campaign, "description", None)
    end_date = getattr(campaign, "end_date", None)

    counts = all_counts.get(campaign_id, {"completed": 0, "total": 0})
    done = int(counts.get("completed", 0) or 0)
    participants = int(counts.get("total", 0) or 0)
    not_started = max(participants - done, 0)
    wip = 0
    pct = int((done / participants) * 100) if participants > 0 else 0
    deadline_text = datetime_to_string(end_date)
    days_left = count_days_left(end_date)
    next_step = step_label_for_campaign(service, campaign)

    with st.container(border=True):
        top_left, top_right = st.columns([5, 1])
        with top_left:
            if is_large_section:
                st.markdown(f"**{name}**")
                st.caption(f"{description or 'No description'} · {participants} participants")
            else:
                st.markdown(compact_campaign_title_html(name), unsafe_allow_html=True)
                st.markdown(compact_campaign_meta_html(f"{participants} participants"), unsafe_allow_html=True)
        with top_right:
            st.markdown(
                status_badge_html(
                    status_meta["label"],
                    status_meta["fg"],
                    status_meta["bg"],
                    compact=not is_large_section,
                ),
                unsafe_allow_html=True,
            )

        if is_large_section:
            progress_col, deadline_col = st.columns([4, 2])
            with progress_col:
                st.caption(f"**Progress** — {pct}% complete")
                st.progress(pct / 100)
            with deadline_col:
                st.caption(f"Deadline: {deadline_text}" if days_left is None else f"Deadline: {deadline_text} ({days_left} days)")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Completed", done)
            m2.metric("In progress", wip)
            m3.metric("Not started", not_started)
            m4.metric("Next Step", next_step)
        else:
            st.markdown(
                compact_campaign_meta_html(f"Progress: {pct}% · Next Step: {next_step} · Deadline: {deadline_text}"),
                unsafe_allow_html=True,
            )

        c_open, _ = st.columns([1, 1])
        with c_open:
            action_label = "Continue →" if status_meta["label"] in ("ACTIVE", "PENDING RESULTS") else "Open →"
            if st.button(action_label, type="primary", key=f"open_{status_meta['section']}_{campaign_id}"):
                select_campaign_and_open(campaign_id)


def render_campaign_sections(service: CampaignService, rows: list[tuple[object, dict]], all_counts: dict) -> None:
    for section_key, section_title in DASHBOARD_SECTIONS:
        section_items = [(campaign, meta) for campaign, meta in rows if meta["section"] == section_key]
        if not section_items:
            continue

        is_large_section = section_key in ("ACTIVE", "PENDING RESULTS")
        st.markdown(section_title_html(section_title), unsafe_allow_html=True)
        for campaign, status_meta in section_items:
            render_campaign_card(service, campaign, status_meta, all_counts, is_large_section)


def render_create_campaign_button() -> None:
    st.markdown("")
    if st.button("+ Create new campaign", key="new_campaign_placeholder"):
        select_campaign_and_open("new")
