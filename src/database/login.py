from datetime import datetime
import uuid
from database.connection import get_connection

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    # Check if the table exists and has the correct schema
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'registered_users'
    """)
    columns = [row[0] for row in cur.fetchall()]
    
    # If table doesn't exist or is missing required columns, recreate it
    if not columns or 'email' not in columns or 'uuid' not in columns:
        cur.execute("DROP TABLE IF EXISTS registered_users")
        cur.execute("""
            CREATE TABLE registered_users (
                id SERIAL PRIMARY KEY,
                uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
                username VARCHAR(255) NOT NULL,
                role VARCHAR(100) NOT NULL,
                email VARCHAR(255),
                login_time TIMESTAMP NOT NULL
            )
        """)
    
    conn.commit()
    cur.close()
    conn.close()


def save_login(username: str, role: str, email: str):
    conn = get_connection()
    cur = conn.cursor()
    
    # Generate a UUID for the user
    user_uuid = str(uuid.uuid4())
    
    # Check if user already exists
    cur.execute(
        "SELECT uuid FROM registered_users WHERE username = %s",
        (username,)
    )
    existing_user = cur.fetchone()
    
    if existing_user:
        # Update existing user's login time
        cur.execute(
            "UPDATE registered_users SET login_time = %s WHERE username = %s",
            (datetime.now(), username)
        )
    else:
        # Insert new user with UUID
        cur.execute(
            "INSERT INTO registered_users (uuid, username, role, email, login_time) VALUES (%s, %s, %s, %s, %s)",
            (user_uuid, username, role, email, datetime.now())
        )
    
    conn.commit()
    cur.close()
    conn.close()
