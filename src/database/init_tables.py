from database.connection import get_connection

def init_org_groups():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'organisation_groups'
                """)
    columns = [row[0] for row in cursor.fetchall()]

    # If table doesn't exist or is missing required columns, recreate it
    if not columns:
        cursor.execute("DROP TABLE IF EXISTS organisation_groups")
        cursor.execute("""
                    CREATE TABLE organisation_groups
                    (
                        id SERIAL PRIMARY KEY,
                        uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
                        name VARCHAR (255) NOT NULL UNIQUE,
                        description TEXT
                    )
                       """)

    connection.commit()
    cursor.close()
    connection.close()
    #TODO: maybe add prerequisites?

def init_org_roles():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'organisation_roles'
    """ )

    columns = [row[0] for row in cursor.fetchall()]

    if not columns:
        cursor.execute("DROP TABLE IF EXISTS organisation_roles")
        cursor.execute("""
            CREATE TABLE organisation_roles
                (
                    id SERIAL PRIMARY KEY,
                    uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
                    name VARCHAR (255) NOT NULL UNIQUE,
                    description TEXT
                )
        """)

    connection.commit()
    cursor.close()
    connection.close()

def init_org_employees():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'organisation_employees'
            )
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            cursor.execute("""
                CREATE TABLE public.organisation_employees
                (
                    id SERIAL PRIMARY KEY,
                    uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    org_role_id INTEGER REFERENCES public.organisation_roles(id),
                    org_role_name2 VARCHAR(255),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

        connection.commit()

    except Exception as e:
        connection.rollback()
        print("init_org_employees ERROR:", e)
        raise
    finally:
        cursor.close()
        connection.close()


def init_employee_groups():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'employee_groups'
            )
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            cursor.execute("""
                CREATE TABLE public.employee_groups
                (
                    employee_id INTEGER NOT NULL REFERENCES public.organisation_employees(id) ON DELETE CASCADE,
                    group_id INTEGER NOT NULL REFERENCES public.organisation_groups(id) ON DELETE CASCADE,
                    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (employee_id, group_id)
                )
            """)

        connection.commit()

    except Exception as e:
        connection.rollback()
        print("init_employee_groups ERROR:", e)
        raise
    finally:
        cursor.close()
        connection.close()


#todo system user, system permissions system roles
#todo + forms, eval databases

def init_databases():
    init_org_groups()
    init_org_roles()
    init_org_employees()
    init_employee_groups()