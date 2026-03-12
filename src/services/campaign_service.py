from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from persistence.db.connection import get_db
from persistence.repository.campaign_repo import CampaignRepository, CampaignRow
from persistence.repository.evaluation_repo import EvaluationRepository
from persistence.repository.form_repo import FormRepository
from persistence.repository.organisation_group_repo import OrganisationGroupRepository
from persistence.repository.organisation_role_repo import OrganisationRoleRepository
from persistence.repository.role_form_defaults_repo import RoleFormDefaultsRepository
from persistence.repository.employee_repo import EmployeeRepository


@dataclass(frozen=True)
class SaveBatchResult:
    success: bool
    error: Optional[str] = None


class CampaignService:
    def __init__(self):
        self.db = get_db()
        self.campaigns = CampaignRepository()
        self.evals = EvaluationRepository()
        self.forms = FormRepository()
        self.groups = OrganisationGroupRepository()
        self.roles = OrganisationRoleRepository()
        self.role_forms = RoleFormDefaultsRepository()
        self.employees = EmployeeRepository()

    # --- Campaign CRUD ---
    def list_campaigns(self) -> List[CampaignRow]:
        with self.db.connection() as conn:
            return self.campaigns.list_campaigns(conn)

    def get_campaign(self, campaign_id: int) -> Optional[CampaignRow]:
        with self.db.connection() as conn:
            return self.campaigns.get_campaign(conn, campaign_id)

    def create_campaign(self, name: str, description: str, start_date: datetime,
                        end_date: Optional[datetime], comment: Optional[str]) -> int:
        with self.db.transaction() as conn:
            return self.campaigns.create_campaign(conn, name, description, start_date, end_date, comment)

    def update_campaign(self, campaign_id: int, name: str, description: str, start_date: datetime,
                        end_date: Optional[datetime], is_active: bool, comment: Optional[str]) -> None:
        with self.db.transaction() as conn:
            self.campaigns.update_campaign(conn, campaign_id, name, description, start_date, end_date, is_active, comment)

    def delete_campaign(self, campaign_id: int) -> None:
        with self.db.transaction() as conn:
            self.campaigns.delete_campaign(conn, campaign_id)

    def toggle_campaign(self, campaign_id: int) -> None:
        with self.db.transaction() as conn:
            self.campaigns.toggle_active(conn, campaign_id)

    # --- Supporting data ---
    def list_forms(self) -> List[Dict[str, Any]]:
        with self.db.connection() as conn:
            return self.forms.list_forms(conn)

    def list_org_roles(self) -> List[Dict[str, Any]]:
        with self.db.connection() as conn:
            return self.roles.list_roles(conn)

    def list_all_groups(self) -> List[Dict[str, Any]]:
        with self.db.connection() as conn:
            return self.groups.list_groups(conn)

    def list_campaign_groups(self, campaign_id: int) -> List[Dict[str, Any]]:
        with self.db.connection() as conn:
            return self.groups.list_campaign_groups(conn, campaign_id)

    def assign_group_to_campaign(self, campaign_id: int, group_id: int) -> None:
        with self.db.transaction() as conn:
            self.groups.assign_to_campaign(conn, campaign_id, group_id)

    def remove_group_from_campaign(self, campaign_id: int, group_id: int) -> None:
        with self.db.transaction() as conn:
            self.groups.remove_from_campaign(conn, campaign_id, group_id)

    def list_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        with self.db.connection() as conn:
            return self.groups.list_group_members(conn, group_id)

    def list_campaign_evaluations(self, campaign_id: int):
        with self.db.connection() as conn:
            return self.evals.list_campaign_evaluations(conn, campaign_id)

    # --- Role-form defaults ---
    def get_role_form_defaults(self, campaign_id: int) -> Dict[Tuple[str, str], int]:
        with self.db.connection() as conn:
            return self.role_forms.get_defaults(conn, campaign_id)

    def upsert_role_form_defaults(self, campaign_id: int, mapping: Dict[Tuple[str, str], int]) -> None:
        with self.db.transaction() as conn:
            self.role_forms.upsert_defaults(conn, campaign_id, mapping)

    # --- Matrix ---
    def get_campaign_group_evaluations(self, campaign_id: int, group_id: int):
        with self.db.connection() as conn:
            return self.evals.get_group_matrix(conn, campaign_id, group_id)

    def save_evaluations_batch(
        self,
        campaign_id: int,
        group_id: int,
        assignments: List[Tuple[int, int]],
        role_form_map: Dict[Tuple[str, str], int],
    ) -> SaveBatchResult:
        try:
            with self.db.transaction() as conn:
                self.evals.delete_group_evaluations(conn, campaign_id, group_id)

                employee_ids = list({a for a, _ in assignments} | {b for _, b in assignments})
                roles_map = self.employees.get_roles_map(conn, employee_ids)

                if not role_form_map:
                    role_form_map = self.role_forms.get_defaults(conn, campaign_id)

                for evaluator_id, evaluatee_id in assignments:
                    er = roles_map.get(evaluator_id)
                    ee = roles_map.get(evaluatee_id)
                    if not er or not ee:
                        raise ValueError(
                            f"Missing organisation role for employee "
                            f"(evaluator_id={evaluator_id} role={er!r}, evaluatee_id={evaluatee_id} role={ee!r})"
                        )

                    form_id = role_form_map.get((er, ee))
                    if not form_id:
                        raise ValueError(f"No default form mapped for {er} -> {ee}")

                    self.evals.insert_evaluation(conn, campaign_id, evaluator_id, evaluatee_id, form_id)

            return SaveBatchResult(success=True)
        except Exception as e:
            return SaveBatchResult(success=False, error=str(e))