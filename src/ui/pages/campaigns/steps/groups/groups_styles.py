import streamlit as st


def status_box_html(success: bool, title: str, detail: str) -> str:
    border = "#86efac" if success else "#fecaca"
    background = "#f0fdf4" if success else "#fef2f2"
    color = "#166534" if success else "#991b1b"
    detail_color = "#166534" if success else "#7f1d1d"
    return f"""
    <div style='border:1px solid {border};background:{background};color:{color};border-radius:10px;padding:10px 12px;margin:4px 0 10px 0;'>
        <span style='font-size:14px;font-weight:600;'>{title}</span><br>
        <span style='font-size:12px;color:{detail_color};'>{detail}</span>
    </div>
    """


def render_status_box(success: bool, title: str, detail: str) -> None:
    st.markdown(status_box_html(success, title, detail), unsafe_allow_html=True)


AVAILABLE_GROUPS_HELP_HTML = """
<style>
    .available-groups-help-wrap { position: relative; display: inline-flex; align-items: center; }
    .available-groups-help-icon {
        display:inline-flex;align-items:center;justify-content:center;
        width:20px;height:20px;border:1px solid #bfdbfe;background:#eff6ff;color:#1d4ed8;
        border-radius:999px;font-size:12px;font-weight:700;line-height:1;
        box-shadow:0 1px 2px rgba(15,23,42,0.08);cursor:default;
    }
    .available-groups-help-tooltip {
        position:absolute;left:50%;transform:translateX(-50%);top:28px;
        min-width:260px;max-width:320px;padding:8px 10px;
        background:#0f172a;color:#f8fafc;border-radius:8px;
        font-size:12px;line-height:1.35;box-shadow:0 6px 20px rgba(15,23,42,0.25);
        opacity:0;visibility:hidden;transition:opacity .14s ease, transform .14s ease;
        pointer-events:none;z-index:20;
    }
    .available-groups-help-wrap:hover .available-groups-help-tooltip {
        opacity:1;visibility:visible;transform:translateX(-50%) translateY(2px);
    }
</style>
<div style='display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 0 8px 0;'>
    <div style='display:flex;align-items:center;gap:8px;'>
        <span style='font-size:16px;font-weight:700;color:#0f172a;'>Available Groups</span>
        <span class='available-groups-help-wrap'>
            <span class='available-groups-help-icon'>?</span>
            <span class='available-groups-help-tooltip'>Groups listed here are not assigned yet. Click Add to include them in this campaign.</span>
        </span>
    </div>
    <span style='font-size:12px;color:#64748b;'>Hover the ? icon for quick help.</span>
</div>
"""


def render_available_groups_header() -> None:
    st.markdown(AVAILABLE_GROUPS_HELP_HTML, unsafe_allow_html=True)
