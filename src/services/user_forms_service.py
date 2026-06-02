from __future__ import annotations

import json
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

    def normalize_questions(self, raw_questions) -> Dict:
        if isinstance(raw_questions, str):
            try:
                raw_questions = json.loads(raw_questions)
            except (json.JSONDecodeError, TypeError, ValueError):
                raw_questions = []

        if isinstance(raw_questions, list):
            return {"sections": [{"title": "General", "questions": raw_questions}]}
        if isinstance(raw_questions, dict) and isinstance(raw_questions.get("sections"), list):
            return raw_questions
        return {"sections": []}

    def save_evaluation_answers(self, evaluation_id: int, answers: Dict) -> bool:
        try:
            with self.db.transaction() as conn:
                rowcount = self.repo.complete_evaluation(conn, evaluation_id, answers)
            return rowcount > 0
        except Exception:
            return False


def create_user_forms_service() -> UserFormsService:
    return UserFormsService(repo=UserFormsRepository())

