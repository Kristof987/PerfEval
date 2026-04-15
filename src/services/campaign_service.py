from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from models.campaign import Campaign
from persistence.db.connection import get_db
from persistence.repository.campaign_repo import CampaignRepository
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
        self.campaigns = CampaignRepository(self.db.session)
        self.evals = EvaluationRepository()
        self.forms = FormRepository()
        self.groups = OrganisationGroupRepository()
        self.roles = OrganisationRoleRepository()
        self.role_forms = RoleFormDefaultsRepository()
        self.employees = EmployeeRepository()

    # --- Campaign CRUD ---
    def list_campaigns(self) -> List[Campaign]:
        with self.db.session() as session:
            campaigns = self.campaigns.list_campaigns()
            # Detach objects from session so they can be used after session closes
            for c in campaigns:
                session.expunge(c)
            return campaigns

    def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        with self.db.session() as session:
            campaign = self.campaigns.get_campaign(campaign_id)
            if campaign is not None:
                session.expunge(campaign)
            return campaign

    def get_campaign_counts(self, campaign_id: int) -> Dict[str, int]:
        """Return completed and total evaluation counts for a single campaign."""
        with self.db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COUNT(id) FILTER (WHERE status = 'completed') AS completed,
                        COUNT(id) AS total
                    FROM evaluation
                    WHERE campaign_id = %s
                """, (campaign_id,))
                row = cur.fetchone()
                return {"completed": row[0] or 0, "total": row[1] or 0}

    def get_all_campaign_counts(self) -> Dict[int, Dict[str, int]]:
        """Return completed and total evaluation counts for all campaigns.

        Returns a dict keyed by campaign_id:
            {campaign_id: {"completed": int, "total": int}}
        """
        with self.db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        campaign_id,
                        COUNT(id) FILTER (WHERE status = 'completed') AS completed,
                        COUNT(id) AS total
                    FROM evaluation
                    GROUP BY campaign_id
                """)
                return {
                    row[0]: {"completed": row[1] or 0, "total": row[2] or 0}
                    for row in cur.fetchall()
                }

    def create_campaign(self, name: str, description: str, start_date: datetime,
                        end_date: Optional[datetime], comment: Optional[str]) -> int:
        return self.campaigns.create_campaign(name, description, start_date, end_date, comment)

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

    def list_campaign_role_names(self, campaign_id: int) -> List[str]:
        """Return distinct role names that are actually present in the campaign's assigned groups."""
        with self.db.connection() as conn:
            campaign_groups = self.groups.list_campaign_groups(conn, campaign_id)
            group_ids = [int(g["id"]) for g in campaign_groups if g.get("id") is not None]

            employee_ids: set[int] = set()
            for group_id in group_ids:
                for member in self.groups.list_group_members(conn, group_id):
                    employee_id = member.get("id")
                    if employee_id is not None:
                        employee_ids.add(int(employee_id))

            if not employee_ids:
                return []

            roles_map = self.employees.get_roles_map(conn, list(employee_ids))
            role_names = sorted({role for role in roles_map.values() if role})
            return role_names

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
