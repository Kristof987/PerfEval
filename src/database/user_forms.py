import json
from typing import Dict, List

from database.connection import get_connection


def get_user_evaluations(employee_id: int) -> List[Dict]:
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT e.id,
                   e.status,
                   e.finish_date,
                   c.id as campaign_id,
                   c.name as campaign_name,
                   f.id as form_id,
                   f.name as form_name,
                   f.description as form_description,
                   f.questions as form_questions,
                   eval_tee.name as evaluatee_name
            FROM evaluation e
            JOIN campaign c ON e.campaign_id = c.id
            JOIN form f ON e.form_id = f.id
            JOIN organisation_employees eval_tee ON e.evaluatee_id = eval_tee.id
            WHERE e.evaluator_id = %s
            ORDER BY c.start_date DESC, eval_tee.name
            """,
            (employee_id,),
        )

        rows = cursor.fetchall()
        evaluations = []
        for row in rows:
            evaluations.append(
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
            )

        return evaluations
    finally:
        cursor.close()
        connection.close()


def save_evaluation_answers(evaluation_id: int, answers: Dict) -> bool:
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE evaluation
            SET answers = %s,
                status = 'completed',
                finish_date = NOW()
            WHERE id = %s
            """,
            (json.dumps(answers), evaluation_id),
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()
