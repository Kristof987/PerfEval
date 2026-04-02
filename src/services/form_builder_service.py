from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from persistence.db.connection import get_db
from persistence.repository.form_repo2 import FormRepository, FormListRow, FormRow

QUESTION_TYPES = {
    "text": (":material/subject:", "Text Response (open-ended)"),
    "multiple_choice": (":material/check_box:", "Multiple Choice"),
    "rating": (":material/star:", "Rating Scale"),
    "slider_labels": (":material/tune:", "Label Slider"),
}

FORM_IMPORT_COLUMNS = [
    "Form Name",
    "Form Description",
    "Section Title",
    "Question Text",
    "Question Type",
    "Required",
    "Options (| separated)",
    "Rating Min",
    "Rating Max",
]


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

    def get_form_import_template_bytes(self) -> bytes:
        template_path = Path("datafiles") / "Form_Import_Template.xlsx"
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        return template_path.read_bytes()

    def import_forms_from_excel(self, uploaded_file) -> list[int]:
        df = pd.read_excel(uploaded_file, sheet_name="form_questions")
        missing_columns = [col for col in FORM_IMPORT_COLUMNS if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing columns: {', '.join(missing_columns)}")

        cleaned_df = df.copy()
        cleaned_df = cleaned_df.dropna(how="all")

        if cleaned_df.empty:
            raise ValueError("The uploaded template is empty.")

        forms_data: dict[str, dict] = {}

        for excel_row_idx, row in cleaned_df.iterrows():
            row_number = int(excel_row_idx) + 2

            form_name = str(row["Form Name"]).strip() if pd.notna(row["Form Name"]) else ""
            form_description = str(row["Form Description"]).strip() if pd.notna(row["Form Description"]) else ""

            section_title = str(row["Section Title"]).strip() if pd.notna(row["Section Title"]) else ""
            question_text = str(row["Question Text"]).strip() if pd.notna(row["Question Text"]) else ""
            qtype = str(row["Question Type"]).strip().lower() if pd.notna(row["Question Type"]) else ""
            required_raw = str(row["Required"]).strip().lower() if pd.notna(row["Required"]) else "yes"

            if not form_name:
                raise ValueError(f"Form Name is required on row {row_number}.")
            if not section_title:
                raise ValueError(f"Section Title is required on row {row_number}.")
            if not question_text:
                raise ValueError(f"Question Text is required on row {row_number}.")
            if qtype not in QUESTION_TYPES:
                raise ValueError(
                    f"Invalid Question Type on row {row_number}: '{qtype}'. "
                    f"Allowed: {', '.join(QUESTION_TYPES.keys())}"
                )

            required = required_raw in {"yes", "true", "1", "y"}

            if form_name not in forms_data:
                forms_data[form_name] = {
                    "description": form_description,
                    "sections_map": {},
                    "sections_in_order": [],
                }
            elif form_description and not forms_data[form_name]["description"]:
                forms_data[form_name]["description"] = form_description

            sections_map: dict[str, dict] = forms_data[form_name]["sections_map"]
            sections_in_order: list[dict] = forms_data[form_name]["sections_in_order"]

            if section_title not in sections_map:
                section = new_section(section_title)
                sections_map[section_title] = section
                sections_in_order.append(section)

            if qtype == "multiple_choice":
                options_raw = str(row["Options (| separated)"]).strip() if pd.notna(row["Options (| separated)"]) else ""
                options = [opt.strip() for opt in options_raw.split("|") if opt.strip()]
                if not options:
                    raise ValueError(f"Options are required for multiple_choice on row {row_number}.")

                question = new_question(
                    text=question_text,
                    qtype=qtype,
                    required=required,
                    options=options,
                )
            elif qtype == "rating":
                if pd.isna(row["Rating Min"]) or pd.isna(row["Rating Max"]):
                    raise ValueError(f"Rating Min and Rating Max are required for rating on row {row_number}.")

                rating_min = int(row["Rating Min"])
                rating_max = int(row["Rating Max"])
                if rating_min >= rating_max:
                    raise ValueError(f"Rating Min must be less than Rating Max on row {row_number}.")

                question = new_question(
                    text=question_text,
                    qtype=qtype,
                    required=required,
                    rating_min=rating_min,
                    rating_max=rating_max,
                )
            elif qtype == "slider_labels":
                options_raw = str(row["Options (| separated)"]).strip() if pd.notna(row["Options (| separated)"]) else ""
                slider_options = [opt.strip() for opt in options_raw.split("|") if opt.strip()]
                if len(slider_options) < 2:
                    raise ValueError(f"At least 2 slider options are required on row {row_number}.")

                question = new_question(
                    text=question_text,
                    qtype=qtype,
                    required=required,
                    slider_options=slider_options,
                )
            else:
                question = new_question(
                    text=question_text,
                    qtype=qtype,
                    required=required,
                )

            sections_map[section_title]["questions"].append(question)

        created_ids: list[int] = []
        with self.db.transaction() as conn:
            for fname, payload in forms_data.items():
                content = {"sections": payload["sections_in_order"]}
                created_id = self.repo.create_form(conn, fname, payload["description"], content)
                created_ids.append(created_id)

        return created_ids

    def import_form_from_excel(self, uploaded_file) -> int:
        created_ids = self.import_forms_from_excel(uploaded_file)
        return created_ids[-1]

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
