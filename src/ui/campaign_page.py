import streamlit as st

# Hardcoded campaign data
CAMPAIGNS = [
    {
        "id": 1,
        "name": "Q1 2024 Performance Review",
        "status": "active",
        "completed": 12,
        "total": 15,
        "created_date": "2024-01-15",
        "deadline": "2024-03-31"
    },
    {
        "id": 2,
        "name": "Annual Performance Evaluation 2023",
        "status": "closed",
        "completed": 45,
        "total": 45,
        "created_date": "2023-12-01",
        "deadline": "2023-12-31"
    },
    {
        "id": 3,
        "name": "Mid-Year Review 2023",
        "status": "closed",
        "completed": 42,
        "total": 44,
        "created_date": "2023-06-01",
        "deadline": "2023-07-15"
    },
    {
        "id": 4,
        "name": "New Employee Onboarding Feedback",
        "status": "active",
        "completed": 5,
        "total": 8,
        "created_date": "2024-02-01",
        "deadline": "2024-02-28"
    },
    {
        "id": 5,
        "name": "Leadership Skills Assessment",
        "status": "closed",
        "completed": 18,
        "total": 20,
        "created_date": "2023-10-01",
        "deadline": "2023-11-30"
    }
]

st.title("📊 Campaign Management")
st.write("Create and manage performance evaluation campaigns")

# Create New Campaign Button
st.write("")
if st.button("➕ Create New Campaign", type="primary", use_container_width=True):
    st.success("✅ New campaign creation form would open here")
    st.info("This feature will allow you to create a new evaluation campaign with custom parameters.")

st.write("")
st.write("---")
st.subheader("Previous Campaigns")

# Display campaigns
for campaign in CAMPAIGNS:
    # Calculate completion percentage
    completion_pct = (campaign["completed"] / campaign["total"]) * 100

    # Status badge color
    status_color = "🟢" if campaign["status"] == "active" else "🔴"
    status_text = campaign["status"].upper()

    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.write(f"### {campaign['name']}")
            st.caption(f"Created: {campaign['created_date']} | Deadline: {campaign['deadline']}")

        with col2:
            st.write("")
            st.write(f"{status_color} **{status_text}**")

        with col3:
            st.write("")
            st.write(f"**{campaign['completed']}/{campaign['total']}**")

        # Progress bar
        st.progress(completion_pct / 100, text=f"Completion: {completion_pct:.0f}%")

        # Action buttons
        col_view, col_edit, col_delete = st.columns([1, 1, 1])

        with col_view:
            if st.button(f"👁️ View", key=f"view_{campaign['id']}", use_container_width=True):
                st.info(f"Viewing details for: {campaign['name']}")

        with col_edit:
            if campaign["status"] == "active":
                if st.button(f"✏️ Edit", key=f"edit_{campaign['id']}", use_container_width=True):
                    st.info(f"Editing: {campaign['name']}")
            else:
                st.button(f"✏️ Edit", key=f"edit_{campaign['id']}", disabled=True, use_container_width=True)

        with col_delete:
            if st.button(f"🗑️", key=f"delete_{campaign['id']}", use_container_width=True):
                st.warning(f"Delete confirmation for: {campaign['name']}")

        st.write("---")

st.write("")
st.info("💡 **Tip:** Active campaigns can be edited, while closed campaigns are archived.")
