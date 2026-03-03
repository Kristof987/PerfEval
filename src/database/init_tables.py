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
                    org_role_name VARCHAR(255),
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

def init_campaign():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
                   SELECT column_name
                   FROM information_schema.columns
                   WHERE table_name = 'campaign'
                   """)

    columns = [row[0] for row in cursor.fetchall()]

    if not columns:
        cursor.execute("DROP TABLE IF EXISTS campaign")
        cursor.execute("""
                       CREATE TABLE campaign
                       (
                           id          SERIAL PRIMARY KEY,
                           uuid        UUID         NOT NULL UNIQUE DEFAULT gen_random_uuid(),
                           name        VARCHAR(255) NOT NULL UNIQUE,
                           description TEXT,
                           start_date  TIMESTAMPTZ  NOT NULL,
                           end_date    TIMESTAMPTZ,
                           is_active   BOOLEAN NOT NULL DEFAULT TRUE,
                           comment  TEXT
                       )
                       """)

    connection.commit()
    cursor.close()
    connection.close()

def init_form():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
                   SELECT column_name
                   FROM information_schema.columns
                   WHERE table_name = 'form'
                   """)

    columns = [row[0] for row in cursor.fetchall()]

    if not columns:
        cursor.execute("DROP TABLE IF EXISTS form")
        cursor.execute("""
                       CREATE TABLE form
                       (
                           id          SERIAL PRIMARY KEY,
                           uuid        UUID         NOT NULL UNIQUE DEFAULT gen_random_uuid(),
                           name        VARCHAR(255) NOT NULL UNIQUE,
                           description TEXT,
                           questions JSONB NOT NULL
                       )
                       """)

    connection.commit()
    cursor.close()
    connection.close()

def init_evaluation():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
                   SELECT column_name
                   FROM information_schema.columns
                   WHERE table_name = 'evaluation'
                   """)

    columns = [row[0] for row in cursor.fetchall()]

    if not columns:
        cursor.execute("DROP TABLE IF EXISTS evaluation")
        cursor.execute("""
                       CREATE TABLE evaluation
                       (
                           id            SERIAL PRIMARY KEY,
                           uuid          UUID         NOT NULL UNIQUE DEFAULT gen_random_uuid(),
                           campaign_id   INTEGER      NOT NULL,
                           evaluator_id  INTEGER      NOT NULL,
                           evaluatee_id  INTEGER      NOT NULL,
                           form_id       INTEGER      NOT NULL,
                           status        VARCHAR(20)  NOT NULL        DEFAULT 'todo',
                           finish_date   TIMESTAMPTZ,
                           answers       JSONB,
                           CONSTRAINT fk_evaluator FOREIGN KEY (evaluator_id) REFERENCES organisation_employees(id),
                           CONSTRAINT fk_evaluatee FOREIGN KEY (evaluatee_id) REFERENCES organisation_employees(id),
                           CONSTRAINT status_check CHECK (status IN ('todo', 'pending', 'completed'))
                       )
                       """)

    connection.commit()
    cursor.close()
    connection.close()

def init_campaign_groups():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'campaign_groups'
            )
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            cursor.execute("""
                CREATE TABLE public.campaign_groups
                (
                    campaign_id INTEGER NOT NULL REFERENCES public.campaign(id) ON DELETE CASCADE,
                    group_id INTEGER NOT NULL REFERENCES public.organisation_groups(id) ON DELETE CASCADE,
                    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (campaign_id, group_id)
                )
            """)

        connection.commit()

    except Exception as e:
        connection.rollback()
        print("init_campaign_groups ERROR:", e)
        raise
    finally:
        cursor.close()
        connection.close()

def init_campaign_role_form_defaults():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'campaign_role_form_defaults'
            )
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            cursor.execute("""
                CREATE TABLE public.campaign_role_form_defaults
                (
                    campaign_id INTEGER NOT NULL REFERENCES public.campaign(id) ON DELETE CASCADE,
                    evaluator_role VARCHAR(255) NOT NULL,
                    evaluatee_role VARCHAR(255) NOT NULL,
                    form_id INTEGER NOT NULL REFERENCES public.form(id) ON DELETE RESTRICT,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (campaign_id, evaluator_role, evaluatee_role)
                )
            """)

        connection.commit()

    except Exception as e:
        connection.rollback()
        print("init_campaign_role_form_defaults ERROR:", e)
        raise
    finally:
        cursor.close()
        connection.close()

def init_system_permissions():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'system_permissions'
            )
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            cursor.execute("""
                CREATE TABLE public.system_permissions
                (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT
                )
            """)

        connection.commit()

    except Exception as e:
        connection.rollback()
        print("init_system_permissions ERROR:", e)
        raise
    finally:
        cursor.close()
        connection.close()

def init_system_roles():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'system_roles'
            )
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            cursor.execute("""
                CREATE TABLE public.system_roles
                (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    system_permission_id INTEGER REFERENCES public.system_permissions(id)
                )
            """)

        connection.commit()

    except Exception as e:
        connection.rollback()
        print("init_system_roles ERROR:", e)
        raise
    finally:
        cursor.close()
        connection.close()

def init_system_users():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'system_users'
            )
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            cursor.execute("""
                CREATE TABLE public.system_users
                (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    username VARCHAR(255) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    employee_id INTEGER REFERENCES public.organisation_employees(id) ON DELETE CASCADE,
                    sys_szerep_id INTEGER REFERENCES public.system_roles(id),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)

        connection.commit()

    except Exception as e:
        connection.rollback()
        print("init_system_users ERROR:", e)
        raise
    finally:
        cursor.close()
        connection.close()

def seed_system_permissions():
    """Seed default system permissions if they don't exist."""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        default_permissions = [
            ("read", "Read-only access to view data"),
            ("write", "Can create and modify data"),
            ("admin", "Full administrative access"),
        ]

        for name, description in default_permissions:
            cursor.execute("""
                INSERT INTO system_permissions (name, description)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (name, description))

        connection.commit()
    except Exception as e:
        connection.rollback()
        print("seed_system_permissions ERROR:", e)
        raise
    finally:
        cursor.close()
        connection.close()


def seed_system_roles():
    """Seed default system roles if they don't exist."""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Get permission IDs
        cursor.execute("SELECT id, name FROM system_permissions")
        permissions = {row[1]: row[0] for row in cursor.fetchall()}

        default_roles = [
            ("Employee", permissions.get("read")),
            ("Team Leader", permissions.get("write")),
            ("HR employee", permissions.get("write")),
            ("Management", permissions.get("read")),
            ("Admin", permissions.get("admin")),
        ]

        for name, permission_id in default_roles:
            cursor.execute("""
                INSERT INTO system_roles (name, system_permission_id)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (name, permission_id))

        connection.commit()
    except Exception as e:
        connection.rollback()
        print("seed_system_roles ERROR:", e)
        raise
    finally:
        cursor.close()
        connection.close()


def seed_admin_user():
    """Create a default admin user if no users exist."""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Check if any system users exist
        cursor.execute("SELECT COUNT(*) FROM system_users")
        user_count = cursor.fetchone()[0]

        if user_count == 0:
            # Get the Admin role ID
            cursor.execute("SELECT id FROM system_roles WHERE name = 'Admin'")
            admin_role = cursor.fetchone()

            if admin_role:
                admin_role_id = admin_role[0]
                # Create default admin user
                cursor.execute("""
                    INSERT INTO system_users (name, username, email, sys_szerep_id)
                    VALUES (%s, %s, %s, %s)
                """, ("System Administrator", "admin", "admin@perfeval.local", admin_role_id))
                connection.commit()
                print("Default admin user created: username='admin', email='admin@perfeval.local'")
    except Exception as e:
        connection.rollback()
        print("seed_admin_user ERROR:", e)
        raise
    finally:
        cursor.close()
        connection.close()


def init_databases():
    init_org_groups()
    init_org_roles()
    init_org_employees()
    init_employee_groups()
    init_campaign()
    init_form()
    init_evaluation()
    init_campaign_groups()
    init_campaign_role_form_defaults()
    init_system_permissions()
    init_system_roles()
    init_system_users()
    # Seed default data
    seed_system_permissions()
    seed_system_roles()
    seed_admin_user()
