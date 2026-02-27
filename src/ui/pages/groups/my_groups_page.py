# app/ui/pages/groups/my_groups_page.py
import streamlit as st

from persistence.db.connection import get_db
from persistence.repository.groups_repo import GroupsRepository
from services.groups_service import GroupsService

st.title("My Groups")

# services wiring (később ezt tedd di.py-ba)
service = GroupsService(get_db(), GroupsRepository())

email = st.session_state.get("email")
if not email:
    st.warning("⚠️ You are not logged in.")
    st.stop()

try:
    employee = service.get_current_employee(email)
except Exception as e:
    st.error(f"Error fetching user data: {e}")
    st.stop()

if not employee:
    st.warning("⚠️ Your employee profile was not found. Please contact an administrator.")
    st.stop()

tab1, tab2 = st.tabs(["My Groups", "Available Groups"])

with tab1:
    st.subheader("Groups You're In")

    try:
        view = service.get_my_groups_view(employee.id)
    except Exception as e:
        st.error(f"Error loading your groups: {e}")
        st.stop()

    if not view.groups:
        st.info("📋 You are not currently a member of any groups. Check the 'Available Groups' tab to join one!")
    else:
        st.write(f"**You are a member of {len(view.groups)} group(s):**")
        st.write("")

        for g in view.groups:
            with st.expander(f"🔹 {g.name}", expanded=False):
                if g.description:
                    st.write(f"**Description:** {g.description}")
                else:
                    st.info("No description available.")

                if g.joined_at:
                    # joined_at could already be datetime; handle both
                    try:
                        st.write(f"**Joined:** {g.joined_at.strftime('%Y-%m-%d %H:%M')}")
                    except Exception:
                        st.write(f"**Joined:** {g.joined_at}")

                members = view.members_by_group.get(g.id, [])
                st.divider()
                st.write(f"**Members ({len(members)}):**")
                for name, mail in members:
                    st.write(f"• {name} ({mail})")

                st.divider()
                if st.button(f"Leave {g.name}", key=f"leave_{g.id}"):
                    try:
                        service.leave_group(employee.id, g.id)
                        st.success(f"✅ You have left {g.name}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error leaving group: {e}")

with tab2:
    st.subheader("Join Groups")
    st.write("Browse and join groups that interest you.")
    st.write("")

    try:
        view = service.get_available_groups_view(employee.id, preview_limit=5)
    except Exception as e:
        st.error(f"Error loading available groups: {e}")
        st.stop()

    if not view.groups:
        st.info("🎉 You are already a member of all available groups!")
    else:
        st.write(f"**{len(view.groups)} group(s) available to join:**")
        st.write("")

        for g in view.groups:
            with st.expander(f"🔹 {g.name} ({g.member_count} members)", expanded=False):
                if g.description:
                    st.write(f"**Description:** {g.description}")
                else:
                    st.info("No description available.")

                preview = view.preview_members_by_group.get(g.id, [])
                if preview:
                    st.divider()
                    st.write(f"**Members ({g.member_count}):**")
                    for name, mail in preview:
                        st.write(f"• {name} ({mail})")
                    if g.member_count > len(preview):
                        st.write(f"... and {g.member_count - len(preview)} more")
                else:
                    st.info("No members yet.")

                st.divider()
                if st.button(f"Join {g.name}", key=f"join_{g.id}"):
                    try:
                        service.join_group(employee.id, g.id)
                        st.success(f"✅ You have joined {g.name}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error joining group: {e}")