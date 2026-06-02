from __future__ import annotations

import streamlit as st

from ui.pages.campaigns.stepper.phase_router import render_phase_content
from ui.pages.campaigns.stepper.session_keys import STEPPER_SCROLL_TO_TOP_KEY, campaign_key
from ui.pages.campaigns.stepper.stepper_state import build_stepper_context, update_current_phase
from ui.pages.campaigns.stepper.stepper_view import render_stepper


def render_campaign_stepper_page() -> None:
    st.set_page_config(layout="wide")
    context = build_stepper_context()

    st.markdown(f"### Campaign flow — {context.campaign_name}")

    new_phase = render_stepper(
        context.current_phase,
        context.meta_text,
        lock_future_steps=True,
        state_key=campaign_key("stepper_pills", context.phase_key, context.widget_nonce),
        max_enabled_step=context.max_enabled_phase,
        completed_until=context.completed_phase,
    )

    if new_phase != context.current_phase and new_phase <= context.max_enabled_phase:
        update_current_phase(context.phase_key, new_phase)
        st.session_state[STEPPER_SCROLL_TO_TOP_KEY] = True
        st.rerun()

    render_phase_content(context.current_phase, context.selected_id, context.campaign_name, context.selected_campaign)


render_campaign_stepper_page()
