import streamlit as st
import json
import pandas as pd
from database.connection import get_connection

st.title("📝 Survey Builder")
st.write("Create and manage performance evaluation questionnaires")

# Initialize session state
if "current_survey_id" not in st.session_state:
    st.session_state.current_survey_id = None

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

def get_all_surveys():
    """Fetch all surveys from database"""
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, uuid, name, description, questions
            FROM form
            ORDER BY id DESC
        """)
        surveys = cursor.fetchall()
        cursor.close()
        connection.close()
        return surveys
    except Exception as e:
        st.error(f"Error fetching surveys: {e}")
        return []

def create_survey(name, description):
    """Create new survey in database"""
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO form (name, description, questions)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (name, description, json.dumps([])))
        survey_id = cursor.fetchone()[0]
        connection.commit()
        cursor.close()
        connection.close()
        return survey_id
    except Exception as e:
        st.error(f"Error creating survey: {e}")
        return None

def get_survey_by_id(survey_id):
    """Get a specific survey by ID"""
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, uuid, name, description, questions
            FROM form
            WHERE id = %s
        """, (survey_id,))
        survey = cursor.fetchone()
        cursor.close()
        connection.close()
        return survey
    except Exception as e:
        st.error(f"Error fetching survey: {e}")
        return None

def add_question_to_survey(survey_id, question):
    """Add a question to an existing survey"""
    try:
        survey = get_survey_by_id(survey_id)
        if not survey:
            return False
        
        # JSONB is already a list from PostgreSQL
        questions = survey[4] if survey[4] else []
        questions.append(question)
        
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE form
            SET questions = %s
            WHERE id = %s
        """, (json.dumps(questions), survey_id))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        st.error(f"Error adding question: {e}")
        return False

def update_survey_questions(survey_id, questions):
    """Update all questions for a survey"""
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE form
            SET questions = %s
            WHERE id = %s
        """, (json.dumps(questions), survey_id))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        st.error(f"Error updating questions: {e}")
        return False

def delete_survey(survey_id):
    """Delete a survey"""
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM form WHERE id = %s", (survey_id,))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        st.error(f"Error deleting survey: {e}")
        return False

st.write("---")

# View Mode Toggle
tab1, tab2 = st.tabs(["📋 Manage Surveys", "➕ Create New Survey"])

with tab2:
    # Create New Survey
    st.subheader("Create New Survey")
    
    with st.form("create_survey"):
        new_title = st.text_input("Survey Title", 
                              placeholder="e.g., Q1 2024 Performance Review")
        new_description = st.text_area("Survey Description",
                                   placeholder="Describe the purpose of this survey...")
        
        if st.form_submit_button("Create Survey", type="primary"):
            if not new_title:
                st.error("❌ Please enter a survey title!")
            else:
                survey_id = create_survey(new_title, new_description)
                if survey_id:
                    st.success(f"✅ Survey '{new_title}' created successfully!")
                    st.session_state.current_survey_id = survey_id
                    st.rerun()

with tab1:
    # List all surveys
    st.subheader("Existing Surveys")
    
    surveys = get_all_surveys()
    
    if not surveys:
        st.info("No surveys created yet. Go to 'Create New Survey' tab to create one.")
    else:
        # Survey selector
        survey_options = {f"{s[2]} (ID: {s[0]})": s[0] for s in surveys}
        selected_survey_key = st.selectbox(
            "Select a survey to edit:",
            options=list(survey_options.keys()),
            index=0 if st.session_state.current_survey_id is None else 
                  list(survey_options.values()).index(st.session_state.current_survey_id) 
                  if st.session_state.current_survey_id in survey_options.values() else 0
        )
        
        selected_survey_id = survey_options[selected_survey_key]
        st.session_state.current_survey_id = selected_survey_id
        
        survey = get_survey_by_id(selected_survey_id)
        
        if survey:
            survey_id, survey_uuid, survey_name, survey_desc, questions_json = survey
            # JSONB is already a list/dict from PostgreSQL, no need to parse
            questions = questions_json if questions_json else []
            
            # Survey info display
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**Title:** {survey_name}")
                if survey_desc:
                    st.write(f"**Description:** {survey_desc}")
                st.write(f"**Questions:** {len(questions)}")
            
            with col2:
                if st.button("🗑️ Delete Survey", key=f"del_survey_{survey_id}"):
                    if delete_survey(survey_id):
                        st.success(f"✅ Survey deleted!")
                        st.session_state.current_survey_id = None
                        st.rerun()
            
            st.write("---")
            
            # Add Question Section
            st.subheader("❓ Add Question")
            
            with st.form(f"add_question_{survey_id}"):
                question_text = st.text_input("Question Text",
                                             placeholder="e.g., How would you rate team collaboration?")
                question_type = st.selectbox("Question Type",
                                            ["Text Response", "Multiple Choice", "Matrix"])
                
                # Show options input for Multiple Choice and Matrix
                options_text = ""
                rows_text = ""
                columns_text = ""
                
                if question_type == "Multiple Choice":
                    st.write("**Multiple Choice Options:**")
                    options_text = st.text_area(
                        "Enter options (one per line)",
                        placeholder="Option 1\nOption 2\nOption 3",
                        help="Enter each option on a new line"
                    )
                elif question_type == "Matrix":
                    st.write("**Matrix Configuration:**")
                    col_matrix1, col_matrix2 = st.columns(2)
                    with col_matrix1:
                        rows_text = st.text_area(
                            "Rows (one per line)",
                            placeholder="Row 1\nRow 2\nRow 3",
                            help="Enter each row label on a new line"
                        )
                    with col_matrix2:
                        columns_text = st.text_area(
                            "Columns (one per line)",
                            placeholder="Column 1\nColumn 2\nColumn 3",
                            help="Enter each column label on a new line"
                        )
                
                required = st.checkbox("Required Question", value=True)
                
                if st.form_submit_button("Add Question"):
                    if not question_text:
                        st.error("❌ Please enter a question text!")
                    elif question_type == "Multiple Choice" and not options_text.strip():
                        st.error("❌ Please enter at least one option for multiple choice questions!")
                    elif question_type == "Matrix" and (not rows_text.strip() or not columns_text.strip()):
                        st.error("❌ Please enter both rows and columns for matrix questions!")
                    else:
                        new_question = {
                            "id": len(questions) + 1,
                            "text": question_text,
                            "type": question_type,
                            "required": required
                        }
                        
                        # Add options for multiple choice
                        if question_type == "Multiple Choice":
                            options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                            new_question["options"] = options
                        # Add rows and columns for matrix
                        elif question_type == "Matrix":
                            rows = [row.strip() for row in rows_text.split('\n') if row.strip()]
                            columns = [col.strip() for col in columns_text.split('\n') if col.strip()]
                            new_question["rows"] = rows
                            new_question["columns"] = columns
                        
                        if add_question_to_survey(survey_id, new_question):
                            st.success(f"✅ Question added!")
                            st.rerun()
            
            st.write("---")
            
            # Display and manage existing questions
            st.subheader("📝 Questions")
            
            if questions:
                st.write(f"**Total Questions:** {len(questions)}")
                st.write("")
                
                for idx, question in enumerate(questions):
                    with st.expander(f"**Question {idx + 1}:** {question['text'][:50]}...", expanded=False):
                        col1, col2 = st.columns([5, 1])
                        
                        with col1:
                            st.write(f"**Question:** {question['text']}")
                            st.write(f"**Type:** {question['type']}")
                            st.write(f"**Required:** {'Yes' if question.get('required', True) else 'No'}")
                            
                            # Display options for multiple choice
                            if question['type'] == "Multiple Choice" and "options" in question:
                                st.write("**Options:**")
                                for opt_idx, option in enumerate(question['options'], 1):
                                    st.write(f"  {opt_idx}. {option}")
                            
                            # Display rows and columns for matrix
                            elif question['type'] == "Matrix":
                                if "rows" in question and "columns" in question:
                                    col_m1, col_m2 = st.columns(2)
                                    with col_m1:
                                        st.write("**Rows:**")
                                        for row_idx, row in enumerate(question['rows'], 1):
                                            st.write(f"  {row_idx}. {row}")
                                    with col_m2:
                                        st.write("**Columns:**")
                                        for col_idx, col in enumerate(question['columns'], 1):
                                            st.write(f"  {col_idx}. {col}")
                        
                        with col2:
                            # Move up button
                            if idx > 0:
                                if st.button("⬆️", key=f"up_{survey_id}_{idx}", help="Move up"):
                                    questions[idx], questions[idx-1] = questions[idx-1], questions[idx]
                                    # Reindex questions
                                    for i, q in enumerate(questions, 1):
                                        q['id'] = i
                                    update_survey_questions(survey_id, questions)
                                    st.rerun()
                            
                            # Move down button
                            if idx < len(questions) - 1:
                                if st.button("⬇️", key=f"down_{survey_id}_{idx}", help="Move down"):
                                    questions[idx], questions[idx+1] = questions[idx+1], questions[idx]
                                    # Reindex questions
                                    for i, q in enumerate(questions, 1):
                                        q['id'] = i
                                    update_survey_questions(survey_id, questions)
                                    st.rerun()
                            
                            # Delete button
                            if st.button("🗑️", key=f"delete_q_{survey_id}_{idx}", help="Delete question"):
                                questions.remove(question)
                                # Reindex questions
                                for i, q in enumerate(questions, 1):
                                    q['id'] = i
                                update_survey_questions(survey_id, questions)
                                st.rerun()
                
                st.write("---")
                
                # Preview Section
                with st.expander("👁️ Preview Survey", expanded=False):
                    st.subheader(survey_name)
                    if survey_desc:
                        st.write(survey_desc)
                    
                    st.write("---")
                    
                    for idx, question in enumerate(questions, 1):
                        question_label = f"{idx}. {question['text']}"
                        if question.get('required', True):
                            question_label += " *"
                        
                        st.write(f"**{question_label}**")
                        
                        if question['type'] == "Text Response":
                            st.text_area("Your answer", key=f"preview_text_{idx}", disabled=True, height=100)
                        elif question['type'] == "Multiple Choice":
                            if "options" in question:
                                st.radio("Select one:", question['options'], key=f"preview_mc_{idx}", disabled=True)
                        elif question['type'] == "Matrix":
                            if "rows" in question and "columns" in question:
                                # Create a scrollable matrix using st.dataframe
                                import pandas as pd
                                
                                # Create empty dataframe with rows and columns
                                matrix_data = {}
                                for col in question['columns']:
                                    matrix_data[col] = [''] * len(question['rows'])
                                
                                df = pd.DataFrame(matrix_data, index=question['rows'])
                                
                                # Display as dataframe with scrolling
                                st.dataframe(
                                    df,
                                    use_container_width=True,
                                    height=min(300, 50 + len(question['rows']) * 35)
                                )
                        
                        st.write("")
            else:
                st.info("👆 No questions added yet. Use the form above to add questions.")
