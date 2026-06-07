from __future__ import annotations

import json
from typing import Any, Dict, List

import pandas as pd

from persistence.db.connection import get_db
from persistence.repository.campaign_repo import CampaignRepository
from persistence.repository.evaluation_repo import EvaluationRepository
from utils.question_schema import normalize_questions


def _build_evaluation_list(rows) -> List[Dict[str, Any]]:
    result = []
    for r in rows:
        answers = r[5]
        if isinstance(answers, str):
            try:
                answers = json.loads(answers)
            except (json.JSONDecodeError, ValueError):
                answers = {}
        elif answers is None:
            answers = {}
        content = normalize_questions(r[7])
        result.append({
            "id":             r[0],
            "evaluator_name": r[1],
            "evaluator_role": r[2] or "Unknown",
            "form_id":        r[3],
            "form_name":      r[4],
            "answers":        answers,
            "finish_date":    r[6],
            "sections":       content["sections"],
        })
    return result


class CampaignResultsService:
    def __init__(self):
        self.db = get_db()
        self.campaigns = CampaignRepository()
        self.evaluations = EvaluationRepository()

    def list_campaign_options(self, empty_label: str = "-- Select a campaign --") -> tuple[list[str], dict[str, int]]:
        with self.db.session() as session:
            campaigns = self.campaigns.list_campaigns(session)
            campaign_rows = [(campaign.name, campaign.id) for campaign in campaigns]

        campaign_options = [empty_label]
        campaign_dict: dict[str, int] = {}
        for campaign_name, campaign_id in campaign_rows:
            campaign_options.append(campaign_name)
            campaign_dict[campaign_name] = campaign_id

        return campaign_options, campaign_dict

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

    def build_employee_qa_json(
        self,
        campaign_id: int,
        campaign_name: str,
        employee_name: str,
        evaluations: List[Dict[str, Any]],
    ) -> dict:
        form_questions: Dict[str, Dict[str, Dict[str, Any]]] = {}

        for evaluation in evaluations:
            form_name = evaluation["form_name"]
            evaluator_role = evaluation.get("evaluator_role") or "Unknown"
            answers = self._parse_answers(evaluation.get("answers"))
            sections: List[Dict[str, Any]] = evaluation.get("sections", [])

            if form_name not in form_questions:
                form_questions[form_name] = {}
                for section in sections:
                    section_title = section.get("title", "General")
                    for question in section.get("questions", []):
                        if not isinstance(question, dict):
                            continue

                        question_id = str(question.get("id", ""))
                        question_type = question.get("type", "text")
                        entry: Dict[str, Any] = {
                            "question": question.get("text", ""),
                            "question_type": question_type,
                            "competence": section_title,
                            "answers": [],
                        }
                        if question_type == "multiple_choice":
                            entry["options"] = question.get("options", [])
                        elif question_type == "slider_labels":
                            entry["options"] = question.get("slider_options", [])

                        form_questions[form_name][question_id] = entry

            for question_id, question_entry in form_questions[form_name].items():
                answer_raw = answers.get(question_id)
                if isinstance(answer_raw, dict):
                    if "rating" in answer_raw:
                        answer_raw = answer_raw["rating"]
                    elif "choice" in answer_raw:
                        answer_raw = answer_raw["choice"]
                    elif "text" in answer_raw:
                        answer_raw = answer_raw["text"]

                if answer_raw is not None and answer_raw != "":
                    question_entry["answers"].append(
                        {
                            "evaluatee_name": employee_name,
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

    def count_completed_evaluations_for_campaign(self, campaign_id: int) -> int:
        with self.db.connection() as conn:
            return self.evaluations.count_completed_evaluations_for_campaign(conn, campaign_id)

    def get_employee_result_export_metadata(self, employee_id: int, campaign_id: int, fallback_name: str) -> Dict[str, Any]:
        with self.db.connection() as conn:
            metadata = self.evaluations.get_employee_result_export_metadata(conn, employee_id, campaign_id)

        return {
            "name": metadata.get("name") or fallback_name,
            "email": metadata.get("email") or "",
            "role": metadata.get("role") or "",
            "submitted_count": metadata.get("submitted_count") or 0,
        }

    def get_evaluations_for_campaign(self, campaign_id: int) -> List[Dict[str, Any]]:
        with self.db.connection() as conn:
            rows = self.evaluations.get_completed_evaluations_for_campaign(conn, campaign_id)
        return _build_evaluation_list(rows)

    def get_evaluations_for_employee(self, employee_id: int, campaign_id: int) -> List[Dict[str, Any]]:
        with self.db.connection() as conn:
            rows = self.evaluations.get_completed_evaluations_for_employee(conn, employee_id, campaign_id)
        return _build_evaluation_list(rows)

