from dataclasses import dataclass

import streamlit as st

from consts.consts import ICONS
from services.campaign_service import CampaignService
from ui.pages.campaigns.helpers.helpers import date_to_datetime
from ui.pages.campaigns.stepper.session_keys import CAMPAIGN_SELECTED_ID_KEY
from ui.pages.campaigns.stepper.stepper_state import set_step_progress


@dataclass(frozen=True)
class CampaignPayload:
    name: str
    description: str
    start_date: object
    end_date: object
    comment: str | None


def validate_campaign_form(name: str, description: str) -> bool:
    if name and description:
        return True

    st.error(f"{ICONS['error']} Please fill in all required fields (marked with *)")
    return False


def build_campaign_payload(name: str, description: str, start_date, end_date, comment: str | None) -> CampaignPayload:
    return CampaignPayload(
        name=name,
        description=description,
        start_date=date_to_datetime(start_date),
        end_date=date_to_datetime(end_date),
        comment=comment if comment else None,
    )


def create_campaign_from_form(name: str, description: str, start_date, end_date, comment: str | None) -> None:
    if not validate_campaign_form(name, description):
        return

    payload = build_campaign_payload(name, description, start_date, end_date, comment)
    _run_campaign_action(
        action=lambda svc: _create_campaign(svc, payload),
        success_message=f"{ICONS['check']} Campaign '{payload.name}' created successfully!",
        error_message="Failed to create campaign.",
    )


def update_campaign_from_form(
    campaign_id: int,
    name: str,
    description: str,
    start_date,
    end_date,
    comment: str | None,
    is_active: bool,
) -> None:
    if not validate_campaign_form(name, description):
        return

    payload = build_campaign_payload(name, description, start_date, end_date, comment)
    _run_campaign_action(
        action=lambda svc: _update_campaign(svc, campaign_id, payload, is_active),
        success_message=f"{ICONS['check']} Campaign '{payload.name}' updated successfully!",
        error_message="Failed to update campaign.",
    )


def _create_campaign(svc: CampaignService, payload: CampaignPayload) -> None:
    campaign_id = svc.create_campaign(
        name=payload.name,
        description=payload.description,
        start_date=payload.start_date,
        end_date=payload.end_date,
        comment=payload.comment,
    )
    st.session_state[CAMPAIGN_SELECTED_ID_KEY] = int(campaign_id)
    set_step_progress(campaign_id, completed_phase=0, current_phase=1)


def _update_campaign(svc: CampaignService, campaign_id: int, payload: CampaignPayload, is_active: bool) -> None:
    svc.update_campaign(
        campaign_id=campaign_id,
        name=payload.name,
        description=payload.description,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_active=is_active,
        comment=payload.comment,
    )
    set_step_progress(campaign_id, completed_phase=0)


def _run_campaign_action(action, success_message: str, error_message: str) -> None:
    try:
        action(CampaignService())
        st.success(success_message)
        st.rerun()
    except Exception as exc:
        st.error(f"{ICONS['error']} {error_message} {exc}")
