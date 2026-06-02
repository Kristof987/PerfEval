import streamlit as st


FORMS_HELP_HTML = """
<style>
    .forms-help-wrap { position: relative; display: inline-flex; align-items: center; }
    .forms-help-icon {
        display:inline-flex;align-items:center;justify-content:center;
        width:20px;height:20px;border:1px solid #bfdbfe;background:#eff6ff;color:#1d4ed8;
        border-radius:999px;font-size:12px;font-weight:700;line-height:1;
        box-shadow:0 1px 2px rgba(15,23,42,0.08);cursor:default;
    }
    .forms-help-tooltip {
        position:absolute;left:50%;transform:translateX(-50%);top:28px;
        min-width:260px;max-width:340px;padding:8px 10px;
        background:#0f172a;color:#f8fafc;border-radius:8px;
        font-size:12px;line-height:1.35;box-shadow:0 6px 20px rgba(15,23,42,0.25);
        opacity:0;visibility:hidden;transition:opacity .14s ease, transform .14s ease;
        pointer-events:none;z-index:20;
    }
    .forms-help-wrap:hover .forms-help-tooltip {
        opacity:1;visibility:visible;transform:translateX(-50%) translateY(2px);
    }
</style>
<div style='display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 0 6px 0;'>
    <div style='display:flex;align-items:center;gap:8px;'>
        <strong>Available role relationships in this campaign:</strong>
        <span class='forms-help-wrap'>
            <span class='forms-help-icon'>?</span>
            <span class='forms-help-tooltip'>Each row is an evaluator role → evaluatee role pair that needs a selected default form.</span>
        </span>
    </div>
</div>
"""


def render_forms_help_header() -> None:
    st.markdown(FORMS_HELP_HTML, unsafe_allow_html=True)


def assignment_status_html(success: bool, selected_pairs: int, total_pairs: int) -> str:
    border = "#86efac" if success else "#fecaca"
    background = "#f0fdf4" if success else "#fef2f2"
    color = "#166534" if success else "#991b1b"
    detail_color = "#166534" if success else "#7f1d1d"
    title = "✅ Default form assignment ready" if success else "❌ Missing default form assignments"
    detail = (
        f"{selected_pairs}/{total_pairs} role relationships are mapped."
        if success
        else f"{selected_pairs}/{total_pairs} role relationships are mapped. Please complete all before saving."
    )
    return f"""
    <div style='border:1px solid {border};background:{background};color:{color};border-radius:10px;padding:10px 12px;margin:4px 0 10px 0;'>
        <span style='font-size:14px;font-weight:600;'>{title}</span><br>
        <span style='font-size:12px;color:{detail_color};'>{detail}</span>
    </div>
    """
