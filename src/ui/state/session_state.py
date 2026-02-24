import streamlit as st

from dataclasses import dataclass, fields

@dataclass(frozen=True)
class Defaults:
    show_edit_dialog: bool = False
    edit_campaign_id: int | None = None
    show_view_dialog: bool = False
    view_campaign_id: int | None = None
    show_delete_confirm: bool = False
    delete_campaign_id: int | None = None
    show_team_assignment: bool = False
    team_campaign_id: int | None = None
    show_evaluation_matrix: bool = False
    matrix_campaign_id: int | None = None
    matrix_group_id: int | None = None

class State:
    @staticmethod
    def init():
        defaults = Defaults()
        for field in fields(defaults):
            key = field.name
            value = getattr(defaults, key)
            st.session_state.setdefault(key, value)