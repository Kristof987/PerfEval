CAMPAIGN_SELECTED_ID_KEY = "campaign_dashboard_selected_id"
CAMPAIGN_PHASE_BY_ID_KEY = "campaign_dashboard_phase_by_id"
CAMPAIGN_COMPLETED_PHASE_BY_ID_KEY = "campaign_dashboard_completed_phase_by_id"
CAMPAIGN_TEAMS_INVALIDATED_BY_ID_KEY = "campaign_dashboard_teams_invalidated_by_id"
STEPPER_LAST_SELECTED_ID_KEY = "campaign_stepper_last_selected_id"
STEPPER_WIDGET_NONCE_BY_ID_KEY = "campaign_stepper_widget_nonce_by_id"
STEPPER_SCROLL_TO_TOP_KEY = "_stepper_scroll_to_top"
STEPPER_PILLS_PREFIX = "stepper_pills"
STEPPER_MATRIX_SELECTIONS_PREFIX = "stepper_matrix_selections"
STEPPER_MATRIX_EDITOR_PREFIX = "stepper_matrix_editor"
STEPPER_PERCENTAGE_PREFIX = "stepper_percentage"
STEPPER_PERCENTAGE_INPUT_PREFIX = "stepper_percentage_input"
STEPPER_ROLE_FORM_MAP_PREFIX = "stepper_role_form_map"
ROLE_FORM_MAP_PREFIX = "role_form_map"
STEPPER_ROLE_FORM_PREFIX = "stepper_role_form"
ROLE_FORM_PREFIX = "role_form"


def campaign_key(*parts: object) -> str:
    return "_".join(str(part) for part in parts)


def stepper_pills_key(phase_key: object) -> str:
    return campaign_key(STEPPER_PILLS_PREFIX, phase_key)


def matrix_selections_key(campaign_id: object, group_id: object) -> str:
    return campaign_key(STEPPER_MATRIX_SELECTIONS_PREFIX, campaign_id, group_id)


def matrix_editor_prefix(matrix_key: str) -> str:
    return campaign_key(STEPPER_MATRIX_EDITOR_PREFIX, matrix_key)


def percentage_key(campaign_id: object, group_id: object) -> str:
    return campaign_key(STEPPER_PERCENTAGE_PREFIX, campaign_id, group_id)


def percentage_input_prefix(key: str) -> str:
    return campaign_key(STEPPER_PERCENTAGE_INPUT_PREFIX, key)


def role_form_map_key(campaign_id: object) -> str:
    return campaign_key(STEPPER_ROLE_FORM_MAP_PREFIX, campaign_id)


def legacy_role_form_map_key(campaign_id: object) -> str:
    return campaign_key(ROLE_FORM_MAP_PREFIX, campaign_id)


def role_form_key(campaign_id: object, evaluator_role: object, evaluatee_role: object) -> str:
    return campaign_key(STEPPER_ROLE_FORM_PREFIX, campaign_id, evaluator_role, evaluatee_role)


def role_form_prefix(campaign_id: object) -> str:
    return campaign_key(STEPPER_ROLE_FORM_PREFIX, campaign_id, "")


def legacy_role_form_prefix(campaign_id: object) -> str:
    return campaign_key(ROLE_FORM_PREFIX, campaign_id, "")
