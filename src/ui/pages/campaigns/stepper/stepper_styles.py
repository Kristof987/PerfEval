STEP_HEADER_HTML = (
    "<p style='margin:0;font-size:14px'>"
    "<span style='color:#10B981;font-weight:600'>Step {step_number}</span>"
    " <span style='color:#aaa'>/ {total_steps}</span>"
    " <span style='color:#aaa;margin:0 6px'>—</span>"
    " <span style='font-weight:500'>{phase_name}</span></p>"
)

STEP_META_RIGHT_HTML = "<p style='margin:0;text-align:right;font-size:13px;color:#888'>{meta_right}</p>"

STEPPER_PROGRESS_HTML = """<div style="height:4px;background:#e5e5e0;border-radius:2px;overflow:hidden;margin-top:-0.5rem;margin-bottom:0.35rem">
    <div style="height:100%;width:{pct}%;border-radius:2px;background:linear-gradient(90deg,#10B981,#185FA5)"></div>
</div>"""

PHASE_CONTENT_DIVIDER_HTML = "<hr style='margin:0.2rem 0 0.35rem 0;border:none;border-top:1px solid #e6e9ef;'>"

SCROLL_TO_TOP_SCRIPT = """<script>window.parent.document.querySelector('section[data-testid="stMain"]').scrollTo({top: 0});</script>"""


def locked_future_step_css(step_index: int) -> str:
    return (
        f"div[role='radiogroup'] > button:nth-child({step_index + 1}) {{"
        f"  opacity: 0.45 !important;"
        f"  pointer-events: none !important;"
        f"  cursor: default !important;"
        f"}}"
    )


def step_header_html(step_number: int, total_steps: int, phase_name: str) -> str:
    return STEP_HEADER_HTML.format(step_number=step_number, total_steps=total_steps, phase_name=phase_name)


def step_meta_right_html(meta_right: str) -> str:
    return STEP_META_RIGHT_HTML.format(meta_right=meta_right)


def stepper_progress_html(pct: int) -> str:
    return STEPPER_PROGRESS_HTML.format(pct=pct)
