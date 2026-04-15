from __future__ import annotations

from typing import Dict, List

from persistence.db.connection import get_db
from persistence.repository.user_forms_repo import UserFormsRepository


class UserFormsService:
    def __init__(self, repo: UserFormsRepository):
        self.db = get_db()
        self.repo = repo

    def get_user_evaluations(self, employee_id: int) -> List[Dict]:
        with self.db.connection() as conn:
            return self.repo.list_user_evaluations(conn, employee_id)

    def save_evaluation_answers(self, evaluation_id: int, answers: Dict) -> bool:
        try:
            with self.db.transaction() as conn:
                rowcount = self.repo.complete_evaluation(conn, evaluation_id, answers)
            return rowcount > 0
        except Exception:
            return False


def create_user_forms_service() -> UserFormsService:
    return UserFormsService(repo=UserFormsRepository())

