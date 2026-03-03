import pandas as pd
import streamlit as st

from consts.consts import TEMPLATE_COLUMNS
from database.connection import get_connection
from database.system_users import get_system_roles


def import_employees_from_template(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> tuple[int, int]:
    df = pd.read_excel(uploaded_file)
    missing_columns = [col for col in TEMPLATE_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns: {', '.join(missing_columns)}")

    roles = get_system_roles()
    role_name_to_id = {role["name"].strip().lower(): role["id"] for role in roles}

    conn = get_connection()
    cursor = conn.cursor()

    inserted = 0
    skipped = 0
    try:
        for _, row in df.iterrows():
            name = str(row["Employee Name"]).strip()
            email = str(row["Employee Email Address"]).strip()
            org_role = str(row["Employee Organisation Role"]).strip()
            system_role = str(row["Employee System Role"]).strip()

            if not name or name.lower() == "nan":
                skipped += 1
                continue

            cursor.execute(
                "SELECT id FROM organisation_employees WHERE LOWER(name) = LOWER(%s)",
                (name,)
            )
            if cursor.fetchone():
                skipped += 1
                continue

            role_id = role_name_to_id.get(system_role.lower())
            if role_id is None:
                skipped += 1
                continue

            cursor.execute(
                "INSERT INTO organisation_employees (name, email, org_role_name) VALUES (%s, %s, %s) RETURNING id",
                (name, email, org_role if org_role and org_role.lower() != "nan" else None),
            )
            employee_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO system_users (name, username, email, sys_szerep_id, employee_id) VALUES (%s, %s, %s, %s, %s)",
                (name, name, email, role_id, employee_id),
            )
            inserted += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return inserted, skipped

def create_new_organisation_group(new_group_name, new_group_description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO organisation_groups (name, description) VALUES (%s, %s)",
        (new_group_name, new_group_description)
    )
    conn.commit()
    cursor.close()
    conn.close()
    st.success(f"✅ Group '{new_group_name}' created successfully!")
    st.rerun()

def list_existing_organisation_groups():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT id, name, description
                   FROM organisation_groups
                   ORDER BY name
                   """)
    groups = cursor.fetchall()
    cursor.close()
    conn.close()
    return groups

def get_group_members(group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT e.id, e.name, e.email
                   FROM organisation_employees e
                            JOIN employee_groups eg ON e.id = eg.employee_id
                   WHERE eg.group_id = %s
                   ORDER BY e.name
                   """, (group_id,))
    members = cursor.fetchall()
    cursor.close()
    conn.close()
    return members

def update_organisation_group_description(group_id, edited_description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE organisation_groups SET description = %s WHERE id = %s",
        (edited_description, group_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    st.success("✅ Description updated!")
    st.rerun()

def delete_employee_from_employee_groups(group_id, employee_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM employee_groups WHERE group_id = %s AND employee_id = %s",
        (group_id, employee_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def find_employees_not_part_of_employee_group(group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT e.id, e.name, e.email
                   FROM organisation_employees e
                   WHERE e.id NOT IN (SELECT employee_id
                                      FROM employee_groups
                                      WHERE group_id = %s)
                   ORDER BY e.name
                   """, (group_id,))
    available_employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return available_employees

def add_employee_to_employee_group(employee_id, group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employee_groups (employee_id, group_id) VALUES (%s, %s)",
        (employee_id, group_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def delete_employee_group(group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM organisation_groups WHERE id = %s", (group_id,))
    conn.commit()
    cursor.close()
    conn.close()

def create_employee_and_add_to_system_users(new_emp_name, new_emp_email, new_emp_role, new_sys_role_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO organisation_employees (name, email, org_role_name) VALUES (%s, %s, %s) RETURNING id",
        (new_emp_name, new_emp_email, new_emp_role if new_emp_role else None)
    )
    employee_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO system_users (name, username, email, sys_szerep_id, employee_id) VALUES (%s, %s, %s, %s, %s)",
        (new_emp_name, new_emp_name, new_emp_email, new_sys_role_id, employee_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_organisation_employees():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT id, name, email, org_role_name
                   FROM organisation_employees
                   ORDER BY name
                   """)
    employees = cursor.fetchall()
    cursor.close()
    conn.close()

    return employees

def get_employees_group_memberships(employee_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT g.id, g.name
                   FROM organisation_groups g
                            JOIN employee_groups eg ON g.id = eg.group_id
                   WHERE eg.employee_id = %s
                   ORDER BY g.name
                   """, (employee_id,))
    employee_groups = cursor.fetchall()
    cursor.close()
    conn.close()
    return employee_groups

def remove_employee_from_employee_groups(emp_id, grp_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM employee_groups WHERE employee_id = %s AND group_id = %s",
        (emp_id, grp_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def find_organisation_groups_employee_not_in(emp_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT g.id, g.name
                   FROM organisation_groups g
                   WHERE g.id NOT IN (SELECT group_id
                                      FROM employee_groups
                                      WHERE employee_id = %s)
                   ORDER BY g.name
                   """, (emp_id,))
    available_groups = cursor.fetchall()
    cursor.close()
    conn.close()

    return available_groups

def add_employee_into_organisation_group(emp_id, group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employee_groups (employee_id, group_id) VALUES (%s, %s)",
        (emp_id, group_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
