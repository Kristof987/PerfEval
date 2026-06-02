import streamlit as st

from ui.pages.campaigns.common.consts import PHASES, PHASE_SHORT
from ui.pages.campaigns.common.styles import append_active_step_highlight, append_background_and_colour_stepper_style
from ui.pages.campaigns.stepper.stepper_styles import (
    locked_future_step_css,
    step_header_html,
    step_meta_right_html,
    stepper_progress_html,
)


def build_stepper_css_rules(
    current: int,
    total_steps: int,
    lock_future_steps: bool,
    max_enabled_step: int | None,
    completed_until: int,
) -> list[str]:
    css_rules = []
    append_background_and_colour_stepper_style(css_rules, completed_until)
    append_active_step_highlight(css_rules, current)

    if lock_future_steps:
        disable_from = (max_enabled_step + 1) if max_enabled_step is not None else (current + 1)
        for step_index in range(disable_from, total_steps):
            css_rules.append(locked_future_step_css(step_index))

    return css_rules


def render_stepper_css(css_rules: list[str]) -> None:
    if css_rules:
        st.markdown(f"<style>\n{chr(10).join(css_rules)}\n</style>", unsafe_allow_html=True)


def render_stepper_header(current: int, meta_right: str = "") -> None:
    head_left, head_right = st.columns([3, 2])
    with head_left:
        st.markdown(step_header_html(current + 1, len(PHASES), PHASES[current]), unsafe_allow_html=True)
    with head_right:
        if meta_right:
            st.markdown(step_meta_right_html(meta_right), unsafe_allow_html=True)


def render_stepper_pills(current: int, state_key: str) -> int:
    selected = st.pills(
        "campaign_step",
        options=list(range(len(PHASES))),
        format_func=lambda step_index: PHASE_SHORT[step_index],
        default=current,
        label_visibility="collapsed",
        key=state_key,
    )
    return selected if selected is not None else current


def render_stepper_progress_bar(current: int) -> None:
    pct = int((current / max(len(PHASES) - 1, 1)) * 100)
    st.markdown(stepper_progress_html(pct), unsafe_allow_html=True)


def render_stepper(
    current: int,
    meta_right: str = "",
    lock_future_steps: bool = False,
    state_key: str = "stepper_pills",
    max_enabled_step: int | None = None,
    completed_until: int = -1,
) -> int:
    css_rules = build_stepper_css_rules(
        current=current,
        total_steps=len(PHASES),
        lock_future_steps=lock_future_steps,
        max_enabled_step=max_enabled_step,
        completed_until=completed_until,
    )
    render_stepper_css(css_rules)
    render_stepper_header(current, meta_right)
    selected = render_stepper_pills(current, state_key)
    render_stepper_progress_bar(current)
    return selected
