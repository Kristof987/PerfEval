from database.connection import get_connection

def init_org_roles():
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

#todo org roles, org employees, system user, system permissions system roles
#todo + forms, eval databases

def init_databases():
    init_org_roles()