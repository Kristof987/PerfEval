from database.login import save_login

def login_user(username: str, role: str, email: str):
    if not username or not role:
        raise ValueError("Username and role required")

    save_login(username, role, email)
