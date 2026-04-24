from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from services.campaign_service import CampaignService


PHASES = [
    "Campaign creation",
    "Team selection",
    "Evaluation matrix",
    "Form assignments",
    "Results",
    "AI evaluation",
    "Closure",
]

PHASE_SHORT = [
    "Create",
    "Teams",
    "Matrix",
    "Forms",
    "Results",
    "AI",
    "Close",
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

if "campaign_dashboard_selected_id" not in st.session_state:
    st.session_state.campaign_dashboard_selected_id = None
if "campaign_dashboard_phase_by_id" not in st.session_state:
    st.session_state.campaign_dashboard_phase_by_id = {}

selected_id = st.session_state.campaign_dashboard_selected_id

if selected_id is None:
    st.info("No campaign selected.")
    if st.button("Back to Campaign Dashboard"):
        st.switch_page("ui/pages/campaigns/campaign_dashboard_page.py")
    st.stop()

campaign_name = "New campaign"
meta_text = "New campaign"

if selected_id != "new":
    svc = CampaignService()
    try:
        campaigns = svc.list_campaigns()
    except Exception as exc:
        st.error(f"Could not load campaign: {exc}")
        if st.button("Back to Campaign Dashboard"):
            st.switch_page("ui/pages/campaigns/campaign_dashboard_page.py")
        st.stop()

    campaign_by_id = {int(getattr(c, "id", 0) or 0): c for c in campaigns}
    selected_campaign = campaign_by_id.get(int(selected_id))

    if selected_campaign is None:
        st.info("Selected campaign no longer exists.")
        if st.button("Back to Campaign Dashboard"):
            st.switch_page("ui/pages/campaigns/campaign_dashboard_page.py")
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

phase_by_id = st.session_state.campaign_dashboard_phase_by_id
phase_key = str(selected_id)
current_phase = int(phase_by_id.get(phase_key, 0))

_stepper(current_phase, meta_text)

selected_phase = st.select_slider(
    "Phase",
    options=list(range(len(PHASES))),
    format_func=lambda i: PHASES[i],
    value=current_phase,
    key=f"campaign_phase_slider_{phase_key}",
)
phase_by_id[phase_key] = int(selected_phase)
st.session_state.campaign_dashboard_phase_by_id = phase_by_id

