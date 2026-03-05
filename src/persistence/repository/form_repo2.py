from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional, List, Tuple


@dataclass(frozen=True)
class FormListRow:
    id: int
    name: str
    description: Optional[str]


@dataclass(frozen=True)
class FormRow:
    id: int
    name: str
    description: Optional[str]
    questions: Any  # could be dict/list/str depending on db history


class FormRepository:
    def list_forms(self, conn) -> List[FormListRow]:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM form ORDER BY id DESC")
            rows = cur.fetchall()
            return [FormListRow(id=r[0], name=r[1], description=r[2]) for r in rows]

    def create_form(self, conn, name: str, description: str, questions_json: dict) -> int:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO form (name, description, questions) VALUES (%s, %s, %s) RETURNING id",
                (name, description, json.dumps(questions_json)),
            )
            return int(cur.fetchone()[0])

    def get_form(self, conn, form_id: int) -> Optional[FormRow]:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description, questions FROM form WHERE id = %s", (form_id,))
            row = cur.fetchone()
            if not row:
                return None
            return FormRow(id=row[0], name=row[1], description=row[2], questions=row[3])

    def update_questions(self, conn, form_id: int, questions_json: dict) -> None:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE form SET questions = %s WHERE id = %s",
                (json.dumps(questions_json), form_id),
            )

    def delete_form(self, conn, form_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM form WHERE id = %s", (form_id,))