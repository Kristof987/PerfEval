import streamlit as st


def matrix_status_html(selected_pairs: int) -> str:
    if selected_pairs > 0:
        return f"""
        <div style='border:1px solid #86efac;background:#f0fdf4;color:#166534;border-radius:10px;padding:10px 12px;margin:4px 0 10px 0;'>
            <span style='font-size:14px;font-weight:600;'>✅ Matrix has assignments</span><br>
            <span style='font-size:12px;color:#166534;'>{selected_pairs} evaluation pair(s) selected.</span>
        </div>
        """

    return """
    <div style='border:1px solid #fecaca;background:#fef2f2;color:#991b1b;border-radius:10px;padding:10px 12px;margin:4px 0 10px 0;'>
        <span style='font-size:14px;font-weight:600;'>❌ Matrix is empty</span><br>
        <span style='font-size:12px;color:#7f1d1d;'>Select at least one evaluation pair before saving.</span>
    </div>
    """


def render_matrix_status(status_placeholder, selected_pairs: int) -> None:
    status_placeholder.markdown(matrix_status_html(selected_pairs), unsafe_allow_html=True)
