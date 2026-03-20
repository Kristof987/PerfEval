from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from persistence.db.connection import get_db
from persistence.repository.form_repo2 import FormRepository, FormListRow, FormRow

QUESTION_TYPES = {
    "text": (":material/subject:", "Text Response (open-ended)"),
    "multiple_choice": (":material/check_box:", "Multiple Choice"),
    "rating": (":material/star:", "Rating Scale"),
    "slider_labels": (":material/tune:", "Label Slider"),
}


def _uid() -> str:
    return str(uuid.uuid4())[:8]


def new_section(title: str) -> dict:
    return {"id": _uid(), "title": title, "questions": []}


def new_question(
    text: str,
    qtype: str,
    required: bool = True,
    options: list | None = None,
    rating_min: int = 1,
    rating_max: int = 5,
    slider_options: list | None = None,
) -> dict:
    q: dict = {"id": _uid(), "text": text, "type": qtype, "required": required}
    if qtype == "multiple_choice":
        q["options"] = options or []
    elif qtype == "rating":
        q["rating_min"] = rating_min
        q["rating_max"] = rating_max
    elif qtype == "slider_labels":
        q["slider_options"] = slider_options or []
    return q


class FormBuilderService:
    """
    Handles:
    - CRUD forms (delegates SQL to repo)
    - content migration (legacy list -> sections dict)
    - JSON parsing if DB returns text
    """

    def __init__(self):
        self.db = get_db()
        self.repo = FormRepository()

    def list_forms(self) -> List[FormListRow]:
        with self.db.connection() as conn:
            return self.repo.list_forms(conn)

    def create_form(self, name: str, description: str) -> int:
        with self.db.transaction() as conn:
            return self.repo.create_form(conn, name, description, {"sections": []})

    def get_form(self, form_id: int) -> Optional[FormRow]:
        with self.db.connection() as conn:
            return self.repo.get_form(conn, form_id)

    def delete_form(self, form_id: int) -> None:
        with self.db.transaction() as conn:
            self.repo.delete_form(conn, form_id)

    def save_content(self, form_id: int, content: dict) -> None:
        with self.db.transaction() as conn:
            self.repo.update_questions(conn, form_id, content)

    # ----- content helpers -----
    def normalize_questions_raw(self, raw: Any) -> Any:
        """
        psycopg2 can return:
        - dict/list if column is json/jsonb and driver decodes
        - str if stored as text/varchar
        - None
        """
        if raw is None:
            return None
        if isinstance(raw, (dict, list)):
            return raw
        if isinstance(raw, str):
            s = raw.strip()
            if not s:
                return None
            try:
                return json.loads(s)
            except Exception:
                return None
        return None

    def migrate_content(self, raw: Any) -> dict:
        raw = self.normalize_questions_raw(raw)

        # legacy: list of questions
        if isinstance(raw, list):
            return {"sections": [{"id": "legacy", "title": "General", "questions": raw}]}

        # current: {"sections":[...]}
        if isinstance(raw, dict) and "sections" in raw and isinstance(raw["sections"], list):
            # sanitize minimal
            for s in raw["sections"]:
                s.setdefault("id", _uid())
                s.setdefault("title", "Section")
                s.setdefault("questions", [])
            return raw

        return {"sections": []}