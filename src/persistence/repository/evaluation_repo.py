from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class EvaluationRow:
    id: int
    uuid: str
    status: str
    finish_date: Optional[str]
    evaluator_name: str
    evaluatee_name: str
    form_name: str


class EvaluationRepository:
    def list_campaign_evaluations(self, conn, campaign_id: int) -> List[EvaluationRow]:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    e.id,
                    e.uuid,
                    e.status,
                    e.finish_date,
                    eval_tor.name as evaluator_name,
                    eval_tee.name as evaluatee_name,
                    f.name as form_name
                FROM evaluation e
                JOIN organisation_employees eval_tor ON e.evaluator_id = eval_tor.id
                JOIN organisation_employees eval_tee ON e.evaluatee_id = eval_tee.id
                JOIN form f ON e.form_id = f.id
                WHERE e.campaign_id = %s
                ORDER BY e.status, eval_tee.name
            """, (campaign_id,))
            return [
                EvaluationRow(
                    id=r[0], uuid=r[1], status=r[2], finish_date=r[3],
                    evaluator_name=r[4], evaluatee_name=r[5], form_name=r[6]
                )
                for r in cur.fetchall()
            ]

    def get_group_matrix(self, conn, campaign_id: int, group_id: int) -> Dict[int, Dict[int, int]]:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.evaluator_id, e.evaluatee_id, e.id
                FROM evaluation e
                JOIN employee_groups eg1 ON e.evaluator_id = eg1.employee_id
                JOIN employee_groups eg2 ON e.evaluatee_id = eg2.employee_id
                WHERE e.campaign_id = %s AND eg1.group_id=%s AND eg2.group_id=%s
            """, (campaign_id, group_id, group_id))
            matrix: Dict[int, Dict[int, int]] = {}
            for evaluator_id, evaluatee_id, eval_id in cur.fetchall():
                matrix.setdefault(evaluator_id, {})[evaluatee_id] = eval_id
            return matrix

    def delete_group_evaluations(self, conn, campaign_id: int, group_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM evaluation
                WHERE campaign_id=%s
                  AND evaluator_id IN (SELECT employee_id FROM employee_groups WHERE group_id=%s)
                  AND evaluatee_id IN (SELECT employee_id FROM employee_groups WHERE group_id=%s)
            """, (campaign_id, group_id, group_id))

    def insert_evaluation(self, conn, campaign_id: int, evaluator_id: int, evaluatee_id: int, form_id: int) -> None:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO evaluation (campaign_id, evaluator_id, evaluatee_id, form_id, status)
                VALUES (%s, %s, %s, %s, 'todo')
            """, (campaign_id, evaluator_id, evaluatee_id, form_id))