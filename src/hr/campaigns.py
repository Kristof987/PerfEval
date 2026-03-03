from database.connection import get_connection
from typing import List, Dict, Optional, Tuple
from datetime import datetime


def get_all_campaigns() -> List[Dict]:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                c.id,
                c.uuid,
                c.name,
                c.description,
                c.start_date,
                c.end_date,
                c.is_active,
                c.comment,
                COUNT(e.id) FILTER (WHERE e.status = 'completed') as completed_count,
                COUNT(e.id) as total_count
            FROM campaign c
            LEFT JOIN evaluation e ON c.id = e.campaign_id
            GROUP BY c.id, c.uuid, c.name, c.description, c.start_date, c.end_date, c.is_active, c.comment
            ORDER BY c.start_date DESC
        """)
        
        rows = cursor.fetchall()
        campaigns = []
        
        for row in rows:
            campaigns.append({
                'id': row[0],
                'uuid': row[1],
                'name': row[2],
                'description': row[3],
                'start_date': row[4],
                'end_date': row[5],
                'is_active': row[6],
                'comment': row[7],
                'completed': row[8] or 0,
                'total': row[9] or 0
            })
        
        return campaigns
        
    except Exception as e:
        print(f"Error fetching campaigns: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_campaign_by_id(campaign_id: int) -> Optional[Dict]:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                c.id,
                c.uuid,
                c.name,
                c.description,
                c.start_date,
                c.end_date,
                c.is_active,
                c.comment,
                COUNT(e.id) FILTER (WHERE e.status = 'completed') as completed_count,
                COUNT(e.id) as total_count
            FROM campaign c
            LEFT JOIN evaluation e ON c.id = e.campaign_id
            WHERE c.id = %s
            GROUP BY c.id, c.uuid, c.name, c.description, c.start_date, c.end_date, c.is_active, c.comment
        """, (campaign_id,))
        
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'uuid': row[1],
                'name': row[2],
                'description': row[3],
                'start_date': row[4],
                'end_date': row[5],
                'is_active': row[6],
                'comment': row[7],
                'completed': row[8] or 0,
                'total': row[9] or 0
            }
        return None
        
    except Exception as e:
        print(f"Error fetching campaign: {e}")
        return None
    finally:
        cursor.close()
        connection.close()


def create_campaign(name: str, description: str, start_date: datetime, 
                   end_date: Optional[datetime] = None, comment: Optional[str] = None) -> Optional[int]:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO campaign (name, description, start_date, end_date, is_active, comment)
            VALUES (%s, %s, %s, %s, TRUE, %s)
            RETURNING id
        """, (name, description, start_date, end_date, comment))
        
        campaign_id = cursor.fetchone()[0]
        connection.commit()
        return campaign_id
        
    except Exception as e:
        connection.rollback()
        print(f"Error creating campaign: {e}")
        return None
    finally:
        cursor.close()
        connection.close()


def update_campaign(campaign_id: int, name: Optional[str] = None, 
                   description: Optional[str] = None, start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None, is_active: Optional[bool] = None,
                   comment: Optional[str] = None) -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        update_fields = []
        params = []
        
        if name is not None:
            update_fields.append("name = %s")
            params.append(name)
        if description is not None:
            update_fields.append("description = %s")
            params.append(description)
        if start_date is not None:
            update_fields.append("start_date = %s")
            params.append(start_date)
        if end_date is not None:
            update_fields.append("end_date = %s")
            params.append(end_date)
        if is_active is not None:
            update_fields.append("is_active = %s")
            params.append(is_active)
        if comment is not None:
            update_fields.append("comment = %s")
            params.append(comment)
        
        if not update_fields:
            return True
        
        params.append(campaign_id)
        query = f"UPDATE campaign SET {', '.join(update_fields)} WHERE id = %s"
        
        cursor.execute(query, params)
        connection.commit()
        return True
        
    except Exception as e:
        connection.rollback()
        print(f"Error updating campaign: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def delete_campaign(campaign_id: int) -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("DELETE FROM evaluation WHERE campaign_id = %s", (campaign_id,))

        cursor.execute("DELETE FROM campaign WHERE id = %s", (campaign_id,))
        
        connection.commit()
        return True
        
    except Exception as e:
        connection.rollback()
        print(f"Error deleting campaign: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def toggle_campaign_status(campaign_id: int) -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            UPDATE campaign 
            SET is_active = NOT is_active 
            WHERE id = %s
        """, (campaign_id,))
        
        connection.commit()
        return True
        
    except Exception as e:
        connection.rollback()
        print(f"Error toggling campaign status: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def get_campaign_evaluations(campaign_id: int) -> List[Dict]:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
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
        
        rows = cursor.fetchall()
        evaluations = []
        
        for row in rows:
            evaluations.append({
                'id': row[0],
                'uuid': row[1],
                'status': row[2],
                'finish_date': row[3],
                'evaluator_name': row[4],
                'evaluatee_name': row[5],
                'form_name': row[6]
            })
        
        return evaluations
        
    except Exception as e:
        print(f"Error fetching campaign evaluations: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_all_forms() -> List[Dict]:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT id, uuid, name, description
            FROM form
            ORDER BY name
        """)
        
        rows = cursor.fetchall()
        forms = []
        
        for row in rows:
            forms.append({
                'id': row[0],
                'uuid': row[1],
                'name': row[2],
                'description': row[3]
            })
        
        return forms
        
    except Exception as e:
        print(f"Error fetching forms: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_organisation_roles() -> List[Dict]:
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT id, name, description
            FROM organisation_roles
            ORDER BY name
        """)

        rows = cursor.fetchall()
        roles = []
        for row in rows:
            roles.append({
                'id': row[0],
                'name': row[1],
                'description': row[2]
            })
        return roles
    except Exception as e:
        print(f"Error fetching organisation roles: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_employee_roles_map(employee_ids: List[int]) -> Dict[int, Optional[str]]:
    if not employee_ids:
        return {}

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT e.id,
                   COALESCE(r.name, e.org_role_name) as role_name
            FROM organisation_employees e
            LEFT JOIN organisation_roles r ON e.org_role_id = r.id
            WHERE e.id = ANY(%s)
        """, (employee_ids,))

        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}
    except Exception as e:
        print(f"Error fetching employee roles: {e}")
        return {}
    finally:
        cursor.close()
        connection.close()


def get_campaign_role_form_defaults(campaign_id: int) -> Dict[Tuple[str, str], int]:
    connection = get_connection()
    cursor = connection.cursor()

    try:
        print(f"[role_form_defaults] fetching campaign_id={campaign_id}")
        cursor.execute("""
            SELECT evaluator_role, evaluatee_role, form_id
            FROM campaign_role_form_defaults
            WHERE campaign_id = %s
        """, (campaign_id,))
        rows = cursor.fetchall()
        print(f"[role_form_defaults] fetched rows={len(rows)}")
        return {(row[0], row[1]): row[2] for row in rows}
    except Exception as e:
        print(f"Error fetching campaign role form defaults: {e}")
        return {}
    finally:
        cursor.close()
        connection.close()


def upsert_campaign_role_form_defaults(
    campaign_id: int,
    role_form_map: Dict[Tuple[str, str], int]
) -> bool:
    print(f"[role_form_defaults] upsert campaign_id={campaign_id} items={len(role_form_map)}")
    if not role_form_map:
        return True

    connection = get_connection()
    cursor = connection.cursor()

    try:
        for (evaluator_role, evaluatee_role), form_id in role_form_map.items():
            cursor.execute("""
                INSERT INTO campaign_role_form_defaults
                    (campaign_id, evaluator_role, evaluatee_role, form_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (campaign_id, evaluator_role, evaluatee_role)
                DO UPDATE SET form_id = EXCLUDED.form_id, updated_at = CURRENT_TIMESTAMP
            """, (campaign_id, evaluator_role, evaluatee_role, form_id))

        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        print(f"Error upserting campaign role form defaults: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def get_all_groups() -> List[Dict]:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT id, uuid, name, description
            FROM organisation_groups
            ORDER BY name
        """)
        
        rows = cursor.fetchall()
        groups = []
        
        for row in rows:
            groups.append({
                'id': row[0],
                'uuid': row[1],
                'name': row[2],
                'description': row[3]
            })
        
        return groups
        
    except Exception as e:
        print(f"Error fetching groups: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_campaign_groups(campaign_id: int) -> List[Dict]:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT g.id, g.uuid, g.name, g.description
            FROM organisation_groups g
            JOIN campaign_groups cg ON g.id = cg.group_id
            WHERE cg.campaign_id = %s
            ORDER BY g.name
        """, (campaign_id,))
        
        rows = cursor.fetchall()
        groups = []
        
        for row in rows:
            groups.append({
                'id': row[0],
                'uuid': row[1],
                'name': row[2],
                'description': row[3]
            })
        
        return groups
        
    except Exception as e:
        print(f"Error fetching campaign groups: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def assign_group_to_campaign(campaign_id: int, group_id: int) -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO campaign_groups (campaign_id, group_id)
            VALUES (%s, %s)
            ON CONFLICT (campaign_id, group_id) DO NOTHING
        """, (campaign_id, group_id))
        
        connection.commit()
        return True
        
    except Exception as e:
        connection.rollback()
        print(f"Error assigning group to campaign: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def remove_group_from_campaign(campaign_id: int, group_id: int) -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM campaign_groups
            WHERE campaign_id = %s AND group_id = %s
        """, (campaign_id, group_id))
        
        connection.commit()
        return True
        
    except Exception as e:
        connection.rollback()
        print(f"Error removing group from campaign: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def get_group_members(group_id: int) -> List[Dict]:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT e.id, e.uuid, e.name, e.email
            FROM organisation_employees e
            JOIN employee_groups eg ON e.id = eg.employee_id
            WHERE eg.group_id = %s
            ORDER BY e.name
        """, (group_id,))
        
        rows = cursor.fetchall()
        employees = []
        
        for row in rows:
            employees.append({
                'id': row[0],
                'uuid': row[1],
                'name': row[2],
                'email': row[3]
            })
        
        return employees
        
    except Exception as e:
        print(f"Error fetching group members: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_campaign_group_evaluations(campaign_id: int, group_id: int) -> Dict:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT
                e.evaluator_id,
                e.evaluatee_id,
                e.id as evaluation_id
            FROM evaluation e
            JOIN employee_groups eg1 ON e.evaluator_id = eg1.employee_id
            JOIN employee_groups eg2 ON e.evaluatee_id = eg2.employee_id
            WHERE e.campaign_id = %s
                AND eg1.group_id = %s
                AND eg2.group_id = %s
        """, (campaign_id, group_id, group_id))
        
        rows = cursor.fetchall()
        matrix = {}
        
        for row in rows:
            evaluator_id = row[0]
            evaluatee_id = row[1]
            evaluation_id = row[2]
            
            if evaluator_id not in matrix:
                matrix[evaluator_id] = {}
            matrix[evaluator_id][evaluatee_id] = evaluation_id
        
        return matrix
        
    except Exception as e:
        print(f"Error fetching evaluation matrix: {e}")
        return {}
    finally:
        cursor.close()
        connection.close()


def create_evaluation(campaign_id: int, evaluator_id: int, evaluatee_id: int, form_id: int = 1) -> Optional[int]:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO evaluation (campaign_id, evaluator_id, evaluatee_id, form_id, status)
            VALUES (%s, %s, %s, %s, 'todo')
            RETURNING id
        """, (campaign_id, evaluator_id, evaluatee_id, form_id))
        
        evaluation_id = cursor.fetchone()[0]
        connection.commit()
        return evaluation_id
        
    except Exception as e:
        connection.rollback()
        print(f"Error creating evaluation: {e}")
        return None
    finally:
        cursor.close()
        connection.close()


def delete_evaluation(evaluation_id: int) -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM evaluation
            WHERE id = %s
        """, (evaluation_id,))
        
        connection.commit()
        return True
        
    except Exception as e:
        connection.rollback()
        print(f"Error deleting evaluation: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def save_evaluations_batch(
    campaign_id: int,
    group_id: int,
    assignments: List[Tuple[int, int]],
    role_form_map: Dict[Tuple[str, str], int]
) -> Tuple[bool, Optional[str]]:
    print(
        "[save_evaluations_batch] start "
        f"campaign_id={campaign_id} group_id={group_id} assignments={len(assignments)}"
    )
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        print("[save_evaluations_batch] deleting existing evaluations")
        cursor.execute("""
            DELETE FROM evaluation
            WHERE campaign_id = %s
            AND evaluator_id IN (
                SELECT employee_id FROM employee_groups WHERE group_id = %s
            )
            AND evaluatee_id IN (
                SELECT employee_id FROM employee_groups WHERE group_id = %s
            )
        """, (campaign_id, group_id, group_id))

        employee_ids = list({evaluator_id for evaluator_id, _ in assignments} | {evaluatee_id for _, evaluatee_id in assignments})
        print(f"[save_evaluations_batch] resolving roles for employee_ids={employee_ids}")
        employee_roles = get_employee_roles_map(employee_ids)
        print(f"[save_evaluations_batch] roles resolved count={len(employee_roles)}")

        if not role_form_map:
            role_form_map = get_campaign_role_form_defaults(campaign_id)
        print(f"[save_evaluations_batch] role_form_map size={len(role_form_map)}")

        for evaluator_id, evaluatee_id in assignments:
            evaluator_role = employee_roles.get(evaluator_id)
            evaluatee_role = employee_roles.get(evaluatee_id)

            if not evaluator_role or not evaluatee_role:
                print(
                    "[save_evaluations_batch] missing role "
                    f"evaluator_id={evaluator_id} evaluator_role={evaluator_role} "
                    f"evaluatee_id={evaluatee_id} evaluatee_role={evaluatee_role}"
                )
                raise ValueError(
                    f"Missing role for employee: "
                    f"evaluator_id={evaluator_id} (role={evaluator_role!r}), "
                    f"evaluatee_id={evaluatee_id} (role={evaluatee_role!r}). "
                    f"Please assign an organisation role to this employee."
                )

            form_id = role_form_map.get((evaluator_role, evaluatee_role))
            if not form_id:
                print(
                    "[save_evaluations_batch] missing form mapping "
                    f"evaluator_role={evaluator_role} evaluatee_role={evaluatee_role}"
                )
                raise ValueError(f"No default form mapped for {evaluator_role} -> {evaluatee_role}")

            cursor.execute("""
                INSERT INTO evaluation (campaign_id, evaluator_id, evaluatee_id, form_id, status)
                VALUES (%s, %s, %s, %s, 'todo')
            """, (campaign_id, evaluator_id, evaluatee_id, form_id))
        
        connection.commit()
        print("[save_evaluations_batch] commit success")
        return True, None
        
    except Exception as e:
        connection.rollback()
        print(f"[save_evaluations_batch] error: {e}")
        return False, str(e)
    finally:
        cursor.close()
        connection.close()
