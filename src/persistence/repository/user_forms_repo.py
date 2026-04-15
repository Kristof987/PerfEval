import json
from typing import Dict, List


class UserFormsRepository:
    def list_user_evaluations(self, conn, employee_id: int) -> List[Dict]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.id,
                       e.status,
                       e.finish_date,
                       c.id AS campaign_id,
                       c.name AS campaign_name,
                       f.id AS form_id,
                       f.name AS form_name,
                       f.description AS form_description,
                       f.questions AS form_questions,
                       eval_tee.name AS evaluatee_name
                FROM evaluation e
                JOIN campaign c ON e.campaign_id = c.id
                JOIN form f ON e.form_id = f.id
                JOIN organisation_employees eval_tee ON e.evaluatee_id = eval_tee.id
                WHERE e.evaluator_id = %s
                ORDER BY c.start_date DESC, eval_tee.name
                """,
                (employee_id,),
            )
            rows = cur.fetchall()

        return [
            {
                "evaluation_id": row[0],
                "status": row[1],
                "finish_date": row[2],
                "campaign_id": row[3],
                "campaign_name": row[4],
                "form_id": row[5],
                "form_name": row[6],
                "form_description": row[7],
                "form_questions": row[8] or [],
                "evaluatee_name": row[9],
            }
            for row in rows
        ]

    def complete_evaluation(self, conn, evaluation_id: int, answers: Dict) -> int:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE evaluation
                SET answers = %s,
                    status = 'completed',
                    finish_date = NOW()
                WHERE id = %s
                """,
                (json.dumps(answers), evaluation_id),
            )
            return cur.rowcount

