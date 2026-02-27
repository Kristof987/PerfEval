import pandas as pd

from consts.consts import TEMPLATE_COLUMNS
from database.connection import get_connection
from database.system_users import get_system_roles


def import_employees_from_template(uploaded_file) -> tuple[int, int]:
    """
    Reads uploaded xlsx and inserts employees.
    Returns: (inserted_count, skipped_count)
    """

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