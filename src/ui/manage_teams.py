import streamlit as st
from database.connection import get_connection

st.title("My Groups")

# Get current user's employee ID from database
try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email
        FROM organisation_employees
        WHERE email = %s
    """, (st.session_state.email,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user_data:
        st.warning("⚠️ Your employee profile was not found. Please contact an administrator.")
        st.stop()
    
    user_id, user_name, user_email = user_data
    
except Exception as e:
    st.error(f"Error fetching user data: {e}")
    st.stop()

# Create tabs for My Groups and Available Groups
tab1, tab2 = st.tabs(["My Groups", "Available Groups"])

# ==================== MY GROUPS TAB ====================
with tab1:
    st.subheader("Groups You're In")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.id, g.name, g.description, eg.joined_at
            FROM organisation_groups g
            JOIN employee_groups eg ON g.id = eg.group_id
            WHERE eg.employee_id = %s
            ORDER BY g.name
        """, (user_id,))
        my_groups = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if my_groups:
            st.write(f"**You are a member of {len(my_groups)} group(s):**")
            st.write("")
            
            for group_id, group_name, group_description, joined_at in my_groups:
                with st.expander(f"🔹 {group_name}", expanded=False):
                    if group_description:
                        st.write(f"**Description:** {group_description}")
                    else:
                        st.info("No description available.")
                    
                    st.write(f"**Joined:** {joined_at.strftime('%Y-%m-%d %H:%M')}")
                    
                    # Get group members
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT e.name, e.email
                        FROM organisation_employees e
                        JOIN employee_groups eg ON e.id = eg.employee_id
                        WHERE eg.group_id = %s
                        ORDER BY e.name
                    """, (group_id,))
                    members = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    
                    st.write("---")
                    st.write(f"**Members ({len(members)}):**")
                    for member_name, member_email in members:
                        st.write(f"• {member_name} ({member_email})")
                    
                    st.write("---")
                    # Leave group button
                    if st.button(f"Leave {group_name}", key=f"leave_{group_id}"):
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                DELETE FROM employee_groups 
                                WHERE employee_id = %s AND group_id = %s
                            """, (user_id, group_id))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success(f"✅ You have left {group_name}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error leaving group: {e}")
        else:
            st.info("📋 You are not currently a member of any groups. Check the 'Available Groups' tab to join one!")
            
    except Exception as e:
        st.error(f"Error loading your groups: {e}")

# ==================== AVAILABLE GROUPS TAB ====================
with tab2:
    st.subheader("Join Groups")
    st.write("Browse and join groups that interest you.")
    st.write("")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.id, g.name, g.description,
                   (SELECT COUNT(*) FROM employee_groups WHERE group_id = g.id) as member_count
            FROM organisation_groups g
            WHERE g.id NOT IN (
                SELECT group_id 
                FROM employee_groups 
                WHERE employee_id = %s
            )
            ORDER BY g.name
        """, (user_id,))
        available_groups = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if available_groups:
            st.write(f"**{len(available_groups)} group(s) available to join:**")
            st.write("")
            
            for group_id, group_name, group_description, member_count in available_groups:
                with st.expander(f"🔹 {group_name} ({member_count} members)", expanded=False):
                    if group_description:
                        st.write(f"**Description:** {group_description}")
                    else:
                        st.info("No description available.")
                    
                    # Get group members (preview)
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT e.name, e.email
                        FROM organisation_employees e
                        JOIN employee_groups eg ON e.id = eg.employee_id
                        WHERE eg.group_id = %s
                        ORDER BY e.name
                        LIMIT 5
                    """, (group_id,))
                    members = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    
                    if members:
                        st.write("---")
                        st.write(f"**Members ({member_count}):**")
                        for member_name, member_email in members:
                            st.write(f"• {member_name} ({member_email})")
                        if member_count > 5:
                            st.write(f"... and {member_count - 5} more")
                    else:
                        st.info("No members yet. Be the first to join!")
                    
                    st.write("---")
                    # Join group button
                    if st.button(f"Join {group_name}", key=f"join_{group_id}"):
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO employee_groups (employee_id, group_id) 
                                VALUES (%s, %s)
                            """, (user_id, group_id))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success(f"✅ You have joined {group_name}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error joining group: {e}")
        else:
            st.info("🎉 You are already a member of all available groups!")
            
    except Exception as e:
        st.error(f"Error loading available groups: {e}")
