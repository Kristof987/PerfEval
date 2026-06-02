from services.campaign_service import CampaignService
from ui.pages.campaigns.common.consts import PHASES
from ui.pages.campaigns.dashboard.dashboard_status import infer_completed_phase as infer_dashboard_completed_phase
from ui.pages.campaigns.helpers.helpers import get


def infer_completed_phase(campaign_obj) -> int:
    try:
        return infer_dashboard_completed_phase(CampaignService(), campaign_obj)
    except Exception:
        return 0


def resolve_completed_phase(selected_id, selected_campaign, completed_by_id: dict) -> int:
    phase_key = str(selected_id)
    if phase_key not in completed_by_id:
        completed_by_id[phase_key] = -1 if selected_id == "new" else infer_completed_phase(selected_campaign)
    elif selected_id != "new":
        inferred_completed = infer_completed_phase(selected_campaign)
        completed_by_id[phase_key] = max(int(completed_by_id.get(phase_key, -1)), int(inferred_completed))
    return int(completed_by_id.get(phase_key, -1))


def max_enabled_phase_for(selected_id, completed_phase: int, invalidated_by_id: dict) -> int:
    max_enabled_phase = min(len(PHASES) - 1, completed_phase + 1)
    if bool(invalidated_by_id.get(str(selected_id), False)):
        max_enabled_phase = max(max_enabled_phase, 2)
    return max_enabled_phase
