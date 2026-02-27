from database.connection import get_connection
from typing import List, Dict, Optional, Tuple
from datetime import datetime

def validate_system_user(username: str) -> Tuple[bool, Optional[Dict]]:
    """
    Validate if a user exists in system_users table by checking username or name.
    Also updates the last_login timestamp.
    
    Args:
        username: The username or name to check
        
    Returns:
        Tuple of (is_valid: bool, user_data: Optional[Dict])
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Check if username matches either username or name field
        cur.execute("""
            SELECT su.id, su.name, su.username, su.email,
                   sr.name as role_name, sr.id as role_id, su.employee_id
            FROM system_users su
            LEFT JOIN system_roles sr ON su.sys_szerep_id = sr.id
            WHERE su.username = %s OR su.name = %s
        """, (username, username))
        
        row = cur.fetchone()
        
        if row:
            user_data = {
                'id': row[0],
                'name': row[1],
                'username': row[2],
                'email': row[3],
                'role_name': row[4],
                'role_id': row[5],
                'employee_id': row[6]
            }
            
            # Update last_login timestamp if column exists
            try:
                cur.execute("""
                    UPDATE system_users
                    SET last_login = %s
                    WHERE id = %s
                """, (datetime.now(), user_data['id']))
                conn.commit()
            except Exception as e:
                # Ignore if last_login column doesn't exist yet
                conn.rollback()
                print(f"Warning: Could not update last_login: {e}")
            
            return True, user_data
        else:
            return False, None
            
    finally:
        cur.close()
        conn.close()

def get_system_roles() -> List[Dict]:
    """Get all system roles"""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT sr.id, sr.name, sp.name as permission_name
            FROM system_roles sr
            LEFT JOIN system_permissions sp ON sr.system_permission_id = sp.id
            ORDER BY sr.name
        """)
        
        roles = []
        for row in cur.fetchall():
            roles.append({
                'id': row[0],
                'name': row[1],
                'permission_name': row[2]
            })
        return roles
    finally:
        cur.close()
        conn.close()

def get_system_permissions() -> List[Dict]:
    """Get all system permissions"""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT id, name, description
            FROM system_permissions
            ORDER BY name
        """)
        
        permissions = []
        for row in cur.fetchall():
            permissions.append({
                'id': row[0],
                'name': row[1],
                'description': row[2]
            })
        return permissions
    finally:
        cur.close()
        conn.close()

def get_all_employees() -> List[Dict]:
    """Get all organization employees"""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT id, name, email, org_role_name
            FROM organisation_employees
            ORDER BY name
        """)
        
        employees = []
        for row in cur.fetchall():
            employees.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'org_role': row[3]
            })
        return employees
    finally:
        cur.close()
        conn.close()

def add_system_user(name: str, username: str, email: str, sys_szerep_id: int, current_user_role: str, employee_id: Optional[int] = None) -> tuple[bool, str]:
    """
    Add a new system user. Only Admin or HR employee can add users.
    
    Args:
        name: Display name of the user
        username: Login username (will be same as name initially)
        email: User email
        sys_szerep_id: System role ID
        current_user_role: Role of the user trying to add (from session_state)
        employee_id: Optional ID of the linked organisation_employees record
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check permissions
    if current_user_role not in ["Admin", "HR employee"]:
        return False, "Only Admin or HR employee can add system users"
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Check if username already exists
        cur.execute("SELECT id FROM system_users WHERE username = %s", (username,))
        if cur.fetchone():
            return False, f"Username '{username}' already exists"
        
        # Check if email already exists
        cur.execute("SELECT id FROM system_users WHERE email = %s", (email,))
        if cur.fetchone():
            return False, f"Email '{email}' already exists"
        
        # Check if employee_id exists if provided
        if employee_id is not None:
            cur.execute("SELECT id FROM organisation_employees WHERE id = %s", (employee_id,))
            if not cur.fetchone():
                return False, f"Employee with ID {employee_id} does not exist"
        
        # Insert new user
        cur.execute("""
            INSERT INTO system_users (name, username, email, sys_szerep_id, employee_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, username, email, sys_szerep_id, employee_id))
        
        conn.commit()
        return True, f"System user '{username}' created successfully"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error creating user: {str(e)}"
    finally:
        cur.close()
        conn.close()

def get_all_system_users() -> List[Dict]:
    """Get all system users with their roles"""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Auto-link system users to employees by matching name/username to employee name
        cur.execute("""
            UPDATE system_users su
            SET employee_id = oe.id
            FROM organisation_employees oe
            WHERE su.employee_id IS NULL
              AND (
                LOWER(su.name) = LOWER(oe.name)
                OR LOWER(su.username) = LOWER(oe.name)
              )
        """)
        conn.commit()

        cur.execute("""
            SELECT su.id, su.name, su.username, su.email,
                   sr.name as role_name, sr.id as role_id,
                   su.created_at, su.employee_id,
                   oe.name as employee_name
            FROM system_users su
            LEFT JOIN system_roles sr ON su.sys_szerep_id = sr.id
            LEFT JOIN organisation_employees oe ON su.employee_id = oe.id
            ORDER BY su.created_at DESC
        """)
        
        users = []
        for row in cur.fetchall():
            users.append({
                'id': row[0],
                'name': row[1],
                'username': row[2],
                'email': row[3],
                'role_name': row[4],
                'role_id': row[5],
                'created_at': row[6],
                'employee_id': row[7],
                'employee_name': row[8]
            })
        return users
    finally:
        cur.close()
        conn.close()

def delete_system_user(user_id: int, current_user_role: str) -> tuple[bool, str]:
    """
    Delete a system user. Only Admin or HR employee can delete users.
    
    Args:
        user_id: ID of the user to delete
        current_user_role: Role of the user trying to delete (from session_state)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check permissions
    if current_user_role not in ["Admin", "HR employee"]:
        return False, "Only Admin or HR employee can delete system users"
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM system_users WHERE id = %s", (user_id,))
        conn.commit()
        
        if cur.rowcount > 0:
            return True, "System user deleted successfully"
        else:
            return False, "User not found"
            
    except Exception as e:
        conn.rollback()
        return False, f"Error deleting user: {str(e)}"
    finally:
        cur.close()
        conn.close()

def add_system_permission(name: str, description: str, current_user_role: str) -> tuple[bool, str]:
    """Add a new system permission (Admin only)"""
    if current_user_role != "Admin":
        return False, "Only Admin can add system permissions"
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO system_permissions (name, description)
            VALUES (%s, %s)
        """, (name, description))
        
        conn.commit()
        return True, f"Permission '{name}' created successfully"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error creating permission: {str(e)}"
    finally:
        cur.close()
        conn.close()

def add_system_role(name: str, permission_id: Optional[int], current_user_role: str) -> tuple[bool, str]:
    """Add a new system role (Admin only)"""
    if current_user_role != "Admin":
        return False, "Only Admin can add system roles"
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO system_roles (name, system_permission_id)
            VALUES (%s, %s)
        """, (name, permission_id))
        
        conn.commit()
        return True, f"Role '{name}' created successfully"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error creating role: {str(e)}"
    finally:
        cur.close()
        conn.close()
