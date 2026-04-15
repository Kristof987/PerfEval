from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple

from persistence.db.connection import get_db
from persistence.repository.org_employees_repo import OrgEmployeesRepository
from persistence.repository.system_permissions_repo import SystemPermissionsRepository
from persistence.repository.system_roles_repo import SystemRolesRepository
from persistence.repository.system_users_repo import SystemUsersRepository


@dataclass(frozen=True)
class LoginResult:
    is_valid: bool
    user_data: Optional[Dict]


class SystemUserService:
    def __init__(
        self,
        users_repo: SystemUsersRepository,
        roles_repo: SystemRolesRepository,
        permissions_repo: SystemPermissionsRepository,
        employees_repo: OrgEmployeesRepository,
    ):
        self.db = get_db()
        self.users_repo = users_repo
        self.roles_repo = roles_repo
        self.permissions_repo = permissions_repo
        self.employees_repo = employees_repo

    def validate_system_user(self, username: str) -> LoginResult:
        with self.db.connection() as conn:
            user = self.users_repo.find_for_login(conn, username)

        if not user:
            return LoginResult(is_valid=False, user_data=None)

        try:
            with self.db.transaction() as conn:
                self.users_repo.update_last_login(conn, user["id"], datetime.now())
        except Exception as exc:
            print(f"Warning: Could not update last_login: {exc}")

        return LoginResult(is_valid=True, user_data=user)

    def list_system_roles(self):
        with self.db.connection() as conn:
            return self.roles_repo.list_roles_with_permissions(conn)

    def list_system_permissions(self):
        with self.db.connection() as conn:
            return self.permissions_repo.list_permissions(conn)

    def list_all_employees(self):
        with self.db.connection() as conn:
            employees = self.employees_repo.list_employees(conn)
            return [
                {
                    "id": e.id,
                    "name": e.name,
                    "email": e.email,
                    "org_role": e.role,
                }
                for e in employees
            ]

    def add_system_user(
        self,
        name: str,
        username: str,
        email: str,
        sys_szerep_id: int,
        current_user_role: str,
        employee_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        if current_user_role not in ["Admin", "HR employee"]:
            return False, "Only Admin or HR employee can add system users"

        try:
            with self.db.transaction() as conn:
                if self.users_repo.username_exists(conn, username):
                    return False, f"Username '{username}' already exists"

                if self.users_repo.email_exists(conn, email):
                    return False, f"Email '{email}' already exists"

                if employee_id is not None and not self.employees_repo.employee_exists_by_id(conn, employee_id):
                    return False, f"Employee with ID {employee_id} does not exist"

                self.users_repo.create_system_user(
                    conn,
                    name=name,
                    username=username,
                    email=email,
                    system_role_id=sys_szerep_id,
                    employee_id=employee_id,
                )

            return True, f"System user '{username}' created successfully"
        except Exception as exc:
            return False, f"Error creating user: {str(exc)}"

    def list_all_system_users(self):
        with self.db.transaction() as conn:
            self.users_repo.sync_employee_links(conn)
            return self.users_repo.list_system_users(conn)

    def delete_system_user(self, user_id: int, current_user_role: str) -> Tuple[bool, str]:
        if current_user_role not in ["Admin", "HR employee"]:
            return False, "Only Admin or HR employee can delete system users"

        try:
            with self.db.transaction() as conn:
                rowcount = self.users_repo.delete_system_user(conn, user_id)

            if rowcount and rowcount > 0:
                return True, "System user deleted successfully"
            return False, "User not found"
        except Exception as exc:
            return False, f"Error deleting user: {str(exc)}"

    def add_system_permission(self, name: str, description: str, current_user_role: str) -> Tuple[bool, str]:
        if current_user_role != "Admin":
            return False, "Only Admin can add system permissions"

        try:
            with self.db.transaction() as conn:
                self.permissions_repo.create_permission(conn, name, description)
            return True, f"Permission '{name}' created successfully"
        except Exception as exc:
            return False, f"Error creating permission: {str(exc)}"

    def add_system_role(self, name: str, permission_id: Optional[int], current_user_role: str) -> Tuple[bool, str]:
        if current_user_role != "Admin":
            return False, "Only Admin can add system roles"

        try:
            with self.db.transaction() as conn:
                self.roles_repo.create_role(conn, name, permission_id)
            return True, f"Role '{name}' created successfully"
        except Exception as exc:
            return False, f"Error creating role: {str(exc)}"


def create_system_user_service() -> SystemUserService:
    return SystemUserService(
        users_repo=SystemUsersRepository(),
        roles_repo=SystemRolesRepository(),
        permissions_repo=SystemPermissionsRepository(),
        employees_repo=OrgEmployeesRepository(),
    )

