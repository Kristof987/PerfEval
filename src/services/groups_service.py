from dataclasses import dataclass
from typing import Dict, List, Tuple

from persistence.repository.groups_repo import GroupsRepository, GroupRow, EmployeeRow
from persistence.db.connection import Database

@dataclass(frozen=True)
class MyGroupsView:
    groups: List[GroupRow]
    members_by_group: Dict[int, List[Tuple[str, str]]]


@dataclass(frozen=True)
class AvailableGroupsView:
    groups: List[GroupRow]
    preview_members_by_group: Dict[int, List[Tuple[str, str]]]


class GroupsService:
    def __init__(self, db: Database, repo: GroupsRepository):
        self.db = db
        self.repo = repo

    def get_current_employee(self, email: str) -> EmployeeRow | None:
        with self.db.connection() as conn:
            return self.repo.get_employee_by_email(conn, email)

    def get_my_groups_view(self, employee_id: int) -> MyGroupsView:
        with self.db.connection() as conn:
            groups = self.repo.get_my_groups(conn, employee_id)
            group_ids = [g.id for g in groups]
            members = self.repo.get_group_members_for_groups(conn, group_ids, limit_per_group=None)
            return MyGroupsView(groups=groups, members_by_group=members)

    def get_available_groups_view(self, employee_id: int, preview_limit: int = 5) -> AvailableGroupsView:
        with self.db.connection() as conn:
            groups = self.repo.get_available_groups(conn, employee_id)
            group_ids = [g.id for g in groups]
            preview = self.repo.get_group_members_for_groups(conn, group_ids, limit_per_group=preview_limit)
            return AvailableGroupsView(groups=groups, preview_members_by_group=preview)

    def join_group(self, employee_id: int, group_id: int) -> None:
        with self.db.transaction() as conn:
            self.repo.join_group(conn, employee_id, group_id)

    def leave_group(self, employee_id: int, group_id: int) -> None:
        with self.db.transaction() as conn:
            self.repo.leave_group(conn, employee_id, group_id)