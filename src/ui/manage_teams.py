import streamlit as st

#Hardcoded for now
TEAMS = {
    "Development Team": {
        "id": 1,
        "members": ["John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis"],
        "lead": "John Smith"
    },
    "Design Team": {
        "id": 2,
        "members": ["Lisa Miller", "David Wilson", "Jennifer Martinez"],
        "lead": "Lisa Miller"
    },
    "Marketing Team": {
        "id": 3,
        "members": ["Robert Garcia", "Jessica Rodriguez", "William Anderson", "Amanda Thomas", "Daniel Lee"],
        "lead": "Robert Garcia"
    },
    "Sales Team": {
        "id": 4,
        "members": ["Christopher Taylor", "Ashley White", "Matthew Harris"],
        "lead": "Christopher Taylor"
    },
    "HR Team": {
        "id": 5,
        "members": ["Michelle Clark", "Brian Lewis", "Stephanie Walker"],
        "lead": "Michelle Clark"
    }
}

st.title("Manage Teams")

st.subheader("Your Teams")
st.info("You are currently not a member of any team.")

st.subheader("Join Teams")
st.write("Click on a team name to view details and join.")

for team_name, team_data in TEAMS.items():
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.expander(f"🔹 {team_name}", expanded=False):
            st.write(f"**Team Lead:** {team_data['lead']}")
            st.write(f"**Members ({len(team_data['members'])}):**")

            for member in team_data['members']:
                st.write(f"  • {member}")
            
            st.write("")
            
            # Join button
            if st.button(f"Join {team_name}", key=f"join_{team_data['id']}"):
                st.success(f"✅ You have requested to join {team_name}!")
                st.info("Your request will be reviewed by the team lead.")

st.write("")
st.write("")
