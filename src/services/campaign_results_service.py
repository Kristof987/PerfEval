from __future__ import annotations

import json
from typing import Any, Dict, List

import pandas as pd

from persistence.db.connection import get_db
from persistence.repository.evaluation_repo import EvaluationRepository
from utils.question_schema import normalize_questions


class CampaignResultsService:
    def __init__(self):
        self.db = get_db()
        self.evaluations = EvaluationRepository()

    @staticmethod
    def _parse_answers(raw_answers) -> Dict[str, Any]:
        if isinstance(raw_answers, str):
            try:
                parsed = json.loads(raw_answers)
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, ValueError):
                return {}
        if isinstance(raw_answers, dict):
            return raw_answers
        return {}

    def build_campaign_qa_json(self, campaign_id: int, campaign_name: str) -> dict:
        with self.db.connection() as conn:
            rows = self.evaluations.get_campaign_completed_qa_rows(conn, campaign_id)

        form_questions: Dict[str, Dict[str, Dict[str, Any]]] = {}

        for row in rows:
            evaluatee_name = row["evaluatee_name"]
            evaluator_role = row.get("evaluator_role") or "Unknown"
            form_name = row["form_name"]
            answers = self._parse_answers(row.get("answers"))
            content = normalize_questions(row.get("questions"))
            sections: List[Dict[str, Any]] = content.get("sections", [])

            if form_name not in form_questions:
                form_questions[form_name] = {}
                for section in sections:
                    section_title = section.get("title", "General")
                    for q in section.get("questions", []):
                        if not isinstance(q, dict):
                            continue
                        q_id = str(q.get("id", ""))
                        q_type = q.get("type", "text")
                        entry: Dict[str, Any] = {
                            "question": q.get("text", ""),
                            "question_type": q_type,
                            "competence": section_title,
                            "answers": [],
                        }
                        if q_type == "multiple_choice":
                            entry["options"] = q.get("options", [])
                        elif q_type == "slider_labels":
                            entry["options"] = q.get("slider_options", [])
                        form_questions[form_name][q_id] = entry

            for q_id, q_entry in form_questions[form_name].items():
                answer_raw = answers.get(q_id)
                if isinstance(answer_raw, dict):
                    if "rating" in answer_raw:
                        answer_raw = answer_raw["rating"]
                    elif "choice" in answer_raw:
                        answer_raw = answer_raw["choice"]
                    elif "text" in answer_raw:
                        answer_raw = answer_raw["text"]

                if answer_raw is not None and answer_raw != "":
                    q_entry["answers"].append(
                        {
                            "evaluatee_name": evaluatee_name,
                            "evaluator_role": evaluator_role,
                            "answer": answer_raw,
                        }
                    )

        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "forms": {form_name: list(questions_by_id.values()) for form_name, questions_by_id in form_questions.items()},
        }

    def get_participants_df_for_campaign(self, campaign_id: int) -> pd.DataFrame:
        with self.db.connection() as conn:
            rows = self.evaluations.get_campaign_participants_overview_rows(conn, campaign_id)
        return pd.DataFrame(rows, columns=["id", "name", "email", "role", "completed_evaluations"])

