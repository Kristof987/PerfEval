from datetime import date

from ui.pages.campaigns.common.consts import PHASES
from ui.pages.campaigns.dashboard.dashboard_state import get_completed_phase, is_teams_invalidated, set_completed_phase
from ui.pages.campaigns.helpers.helpers import to_date


def get_value(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def infer_completed_phase(service, campaign_obj) -> int:
    campaign_id = int(get_value(campaign_obj, "id", 0) or 0)
    if campaign_id <= 0:
        return -1

    groups = service.list_campaign_groups(campaign_id)
    has_groups = bool(groups)

    has_full_matrix_coverage = False
    if has_groups:
        has_full_matrix_coverage = True
        for group in groups:
            group_id = int(get_value(group, "id", 0) or 0)
            if group_id <= 0:
                has_full_matrix_coverage = False
                break
            matrix = service.get_campaign_group_evaluations(campaign_id, group_id)
            has_any_assignment = any(bool(evaluatees) for evaluatees in matrix.values())
            if not has_any_assignment:
                has_full_matrix_coverage = False
                break

    evaluations = service.list_campaign_evaluations(campaign_id)
    has_any_completion = any(str(get_value(evaluation, "status", "")).lower() == "completed" for evaluation in evaluations)

    role_defaults = service.get_role_form_defaults(campaign_id) if has_groups else {}
    has_role_defaults = any(form_id is not None for form_id in role_defaults.values()) if role_defaults else False
    has_closed_campaign = not bool(get_value(campaign_obj, "is_active", True))

    completed_phase = 0
    if has_groups:
        completed_phase = 1
    if has_role_defaults:
        completed_phase = 2
    if has_full_matrix_coverage:
        completed_phase = 3
    if has_any_completion:
        completed_phase = 5
    if has_closed_campaign:
        completed_phase = 6
    if is_teams_invalidated(campaign_id):
        completed_phase = min(completed_phase, 1)

    return completed_phase


def step_label_for_campaign(service, campaign) -> str:
    campaign_id = int(get_value(campaign, "id", 0) or 0)
    if campaign_id <= 0:
        return PHASES[0]

    try:
        completed_phase = infer_completed_phase(service, campaign)
        set_completed_phase(campaign_id, completed_phase)
    except Exception:
        completed_phase = get_completed_phase(campaign_id)

    next_step_index = min(len(PHASES) - 1, max(0, int(completed_phase) + 1))
    return PHASES[next_step_index]


def campaign_status_meta(campaign, completed: int, total: int) -> dict:
    today = date.today()
    end_date = to_date(get_value(campaign, "end_date"))
    is_active = bool(get_value(campaign, "is_active", False))
    comment = str(get_value(campaign, "comment") or "")
    is_pending_results = "[PENDING_RESULTS]" in comment
    is_closed_marked = "[CLOSED]" in comment
    completion_pct = (completed / total * 100) if total > 0 else 0

    if is_closed_marked and not is_active:
        return {"label": "CLOSED", "fg": "#991b1b", "bg": "#fee2e2", "section": "CLOSED"}
    if ((end_date is not None and end_date < today) or completion_pct >= 100) and not is_active:
        return {"label": "CLOSED", "fg": "#991b1b", "bg": "#fee2e2", "section": "CLOSED"}
    if is_pending_results:
        return {"label": "PENDING RESULTS", "fg": "#7c2d12", "bg": "#ffedd5", "section": "PENDING RESULTS"}
    if is_active:
        return {"label": "ACTIVE", "fg": "#065f46", "bg": "#dcfce7", "section": "ACTIVE"}
    return {"label": "INACTIVE", "fg": "#334155", "bg": "#e2e8f0", "section": "INACTIVE"}
