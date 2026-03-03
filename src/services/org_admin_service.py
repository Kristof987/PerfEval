from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from persistence.db.connection import get_db
from persistence.repository.org_groups_repo import OrgGroupsRepository, OrgGroup
from persistence.repository.org_employees_repo import OrgEmployeesRepository, OrgEmployee
from persistence.repository.system_roles_repo import SystemRolesRepository, SystemRole
from integrations.excel.employee_importer import import_employees_from_template


@dataclass(frozen=True)
class GroupsView:
    groups: List[OrgGroup]


@dataclass(frozen=True)
class EmployeesView:
    employees: List[OrgEmployee]


class OrgAdminService:
    def __init__(
        self,
        groups_repo: OrgGroupsRepository,
        employees_repo: OrgEmployeesRepository,
        roles_repo: SystemRolesRepository,
    ):
        self.db = get_db()
        self.groups_repo = groups_repo
        self.employees_repo = employees_repo
        self.roles_repo = roles_repo

    def list_groups(self) -> GroupsView:
        with self.db.connection() as conn:
            return GroupsView(groups=self.groups_repo.list_groups(conn))

    def create_group(self, name: str, description: str | None) -> None:
        with self.db.transaction() as conn:
            self.groups_repo.create_group(conn, name, description)

    def update_group_description(self, group_id: int, description: str | None) -> None:
        with self.db.transaction() as conn:
            self.groups_repo.update_group_description(conn, group_id, description)

    def delete_group(self, group_id: int) -> None:
        with self.db.transaction() as conn:
            self.groups_repo.delete_group(conn, group_id)

    def get_group_members(self, group_id: int) -> List[Tuple[int, str, str]]:
        with self.db.connection() as conn:
            return self.groups_repo.list_group_members(conn, group_id)

    def get_employees_not_in_group(self, group_id: int) -> List[Tuple[int, str, str]]:
        with self.db.connection() as conn:
            return self.groups_repo.list_employees_not_in_group(conn, group_id)

    def add_member_to_group(self, group_id: int, employee_id: int) -> None:
        with self.db.transaction() as conn:
            self.groups_repo.add_member(conn, group_id, employee_id)

    def remove_member_from_group(self, group_id: int, employee_id: int) -> None:
        with self.db.transaction() as conn:
            self.groups_repo.remove_member(conn, group_id, employee_id)

    def list_employees(self) -> EmployeesView:
        with self.db.connection() as conn:
            return EmployeesView(employees=self.employees_repo.list_employees(conn))

    def list_employee_groups(self, employee_id: int) -> List[Tuple[int, str]]:
        with self.db.connection() as conn:
            return self.employees_repo.list_employee_groups(conn, employee_id)

    def list_groups_employee_not_in(self, employee_id: int) -> List[Tuple[int, str]]:
        with self.db.connection() as conn:
            return self.employees_repo.list_groups_employee_not_in(conn, employee_id)

    def remove_employee_from_group(self, employee_id: int, group_id: int) -> None:
        with self.db.transaction() as conn:
            self.employees_repo.remove_employee_from_group(conn, employee_id, group_id)

    def list_system_roles(self) -> List[SystemRole]:
        with self.db.connection() as conn:
            return self.roles_repo.list_roles(conn)

    def import_employees(self, uploaded_file) -> tuple[int, int]:
        return import_employees_from_template(uploaded_file)

    def get_employee_template_path(self) -> Path:
        return Path("datafiles") / "Employee_Template.xlsx"