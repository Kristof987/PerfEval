import streamlit as st

st.title("📝 Survey Builder")
st.write("Create and manage performance evaluation questionnaires")

# Initialize session state for the current survey being built
if "survey_title" not in st.session_state:
    st.session_state.survey_title = ""
    st.session_state.survey_description = ""
    st.session_state.selected_groups = []
    st.session_state.sections = []

# Hardcoded groups for testing
AVAILABLE_GROUPS = [
    "Development Team",
    "Design Team",
    "Marketing Team",
    "Sales Team",
    "HR Team",
    "Management",
    "All Employees"
]

st.write("---")

# Survey Basic Information
st.subheader("📋 Survey Information")

with st.form("survey_basic_info"):
    title = st.text_input("Survey Title", value=st.session_state.survey_title, 
                          placeholder="e.g., Q1 2024 Performance Review")
    description = st.text_area("Survey Description", value=st.session_state.survey_description,
                               placeholder="Describe the purpose of this survey...")
    
    st.write("**Assign to Groups:**")
    selected_groups = st.multiselect(
        "Select target groups", 
        AVAILABLE_GROUPS,
        default=st.session_state.selected_groups
    )
    
    if st.form_submit_button("💾 Save Survey Info"):
        st.session_state.survey_title = title
        st.session_state.survey_description = description
        st.session_state.selected_groups = selected_groups
        st.success("✅ Survey information saved!")

st.write("---")

# Sections Management
st.subheader("📑 Survey Sections")

# Add new section
with st.expander("➕ Add New Section", expanded=False):
    with st.form("add_section"):
        section_title = st.text_input("Section Title", placeholder="e.g., Communication Skills")
        section_description = st.text_area("Section Description", 
                                            placeholder="Describe what this section evaluates...")
        
        if st.form_submit_button("Add Section"):
            new_section = {
                "id": len(st.session_state.sections) + 1,
                "title": section_title,
                "description": section_description,
                "questions": []
            }
            st.session_state.sections.append(new_section)
            st.success(f"✅ Added section: {section_title}")
            st.rerun()

# Display existing sections
if st.session_state.sections:
    st.write(f"**Total Sections:** {len(st.session_state.sections)}")
    
    for idx, section in enumerate(st.session_state.sections):
        with st.expander(f"**Section {idx + 1}:** {section['title']}", expanded=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"**Description:** {section['description']}")
                st.write(f"**Questions:** {len(section['questions'])}")
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_section_{section['id']}"):
                    st.session_state.sections.remove(section)
                    st.rerun()
            
            st.write("")
            
            # Add question to this section
            with st.form(f"add_question_{section['id']}"):
                st.write("**Add Question:**")
                question_text = st.text_input("Question", 
                                               placeholder="e.g., How would you rate team collaboration?",
                                               key=f"q_text_{section['id']}")
                question_type = st.selectbox("Response Type", 
                                              ["Rating (1-5)", "Text", "Yes/No", "Multiple Choice"],
                                              key=f"q_type_{section['id']}")
                
                if st.form_submit_button("Add Question"):
                    new_question = {
                        "id": len(section['questions']) + 1,
                        "text": question_text,
                        "type": question_type
                    }
                    section['questions'].append(new_question)
                    st.success(f"✅ Question added!")
                    st.rerun()
            
            # Display questions
            if section['questions']:
                st.write("**Questions in this section:**")
                for q_idx, question in enumerate(section['questions']):
                    col_q1, col_q2, col_q3 = st.columns([5, 2, 1])
                    with col_q1:
                        st.write(f"{q_idx + 1}. {question['text']}")
                    with col_q2:
                        st.caption(f"Type: {question['type']}")
                    with col_q3:
                        if st.button("❌", key=f"del_q_{section['id']}_{question['id']}"):
                            section['questions'].remove(question)
                            st.rerun()
else:
    st.info("👆 No sections added yet. Click 'Add New Section' to get started.")

st.write("---")

# Survey Summary and Actions
st.subheader("📊 Survey Summary")

if st.session_state.survey_title:
    col_sum1, col_sum2 = st.columns(2)
    
    with col_sum1:
        st.metric("Survey Title", st.session_state.survey_title)
        st.metric("Sections", len(st.session_state.sections))
    
    with col_sum2:
        st.metric("Target Groups", len(st.session_state.selected_groups))
        total_questions = sum(len(s['questions']) for s in st.session_state.sections)
        st.metric("Total Questions", total_questions)
    
    st.write("")
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("💾 Save Survey", type="primary", use_container_width=True):
            st.success("✅ Survey saved successfully!")
            st.info("Survey data would be saved to database here.")
    
    with col_btn2:
        if st.button("👁️ Preview", use_container_width=True):
            st.info("📄 Preview mode would open here")
    
    with col_btn3:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.survey_title = ""
            st.session_state.survey_description = ""
            st.session_state.selected_groups = []
            st.session_state.sections = []
            st.rerun()
else:
    st.warning("⚠️ Please fill in the survey information above to see the summary.")
