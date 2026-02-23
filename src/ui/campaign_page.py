import streamlit as st
import pandas as pd
import random
from datetime import datetime
from hr.campaigns import (
    get_all_campaigns,
    get_campaign_by_id,
    create_campaign,
    update_campaign,
    delete_campaign,
    toggle_campaign_status,
    get_campaign_evaluations,
    get_all_groups,
    get_all_forms,
    get_campaign_groups,
    assign_group_to_campaign,
    remove_group_from_campaign,
    get_group_members,
    get_campaign_group_evaluations,
    create_evaluation,
    delete_evaluation,
    save_evaluations_batch
)

# Material icon mapping for consistent icon usage
ICONS = {
    "dashboard": ":material/monitoring:",
    "add": ":material/add:",
    "edit": ":material/edit:", 
    "delete": ":material/delete:",
    "view": ":material/visibility:",
    "teams": ":material/groups:",
    "matrix": ":material/grid_on:",
    "save": ":material/save:",
    "close": ":material/close:",
    "check": ":material/check_circle:",
    "error": ":material/cancel:",
    "warning": ":material/warning:",
    "info": ":material/info:",
    "active": ":material/check_circle:",
    "inactive": ":material/cancel:",
    "office": ":material/business:",
    "pause": ":material/pause:",
    "pending": ":material/schedule:",
    "help": ":material/help:",
    "play": ":material/play_arrow:",
    "dice": ":material/casino:",
    "list": ":material/list:",
    "lightbulb": ":material/lightbulb:",
    "select_all": ":material/select_all:"
}

# Get query parameters
query_params = st.query_params

# Initialize session state for dialog management
# show_create_dialog is now handled by query params
if 'show_edit_dialog' not in st.session_state:
    st.session_state.show_edit_dialog = False
if 'edit_campaign_id' not in st.session_state:
    st.session_state.edit_campaign_id = None
if 'show_view_dialog' not in st.session_state:
    st.session_state.show_view_dialog = False
if 'view_campaign_id' not in st.session_state:
    st.session_state.view_campaign_id = None
if 'show_delete_confirm' not in st.session_state:
    st.session_state.show_delete_confirm = False
if 'delete_campaign_id' not in st.session_state:
    st.session_state.delete_campaign_id = None
if 'show_team_assignment' not in st.session_state:
    st.session_state.show_team_assignment = False
if 'team_campaign_id' not in st.session_state:
    st.session_state.team_campaign_id = None
if 'show_evaluation_matrix' not in st.session_state:
    st.session_state.show_evaluation_matrix = False
if 'matrix_campaign_id' not in st.session_state:
    st.session_state.matrix_campaign_id = None
if 'matrix_group_id' not in st.session_state:
    st.session_state.matrix_group_id = None

st.write(st.session_state)

st.title(f"{ICONS['dashboard']} Campaign Management")
st.write("Create and manage performance evaluation campaigns")

# Create New Campaign Dialog
if query_params.get("create") == "true":
    with st.form("create_campaign_form"):
        st.subheader(f"{ICONS['add']} Create New Campaign")
        
        name = st.text_input("Campaign Name*", placeholder="e.g., Q1 2024 Performance Review")
        description = st.text_area("Description*", placeholder="Enter campaign description")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date*", value=datetime.now())
        with col2:
            end_date = st.date_input("End Date", value=None)
        
        comment = st.text_area("Additional Comments (optional)", placeholder="Any additional notes about this campaign")
        
        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button("Create Campaign", type="primary", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)
        
        if submitted:
            if not name or not description:
                st.error(f"{ICONS['error']} Please fill in all required fields (marked with *)")
            else:
                # Convert dates to datetime
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.min.time()) if end_date else None
                
                campaign_id = create_campaign(
                    name=name,
                    description=description,
                    start_date=start_datetime,
                    end_date=end_datetime,
                    comment=comment if comment else None
                )
                
                if campaign_id:
                    st.success(f"{ICONS['check']} Campaign '{name}' created successfully!")
                    query_params.clear()
                    st.rerun()
                else:
                    st.error(f"{ICONS['error']} Failed to create campaign. Campaign name might already exist.")
        
        if cancelled:
            query_params.clear()
            st.rerun()

# Edit Campaign Dialog
elif st.session_state.show_edit_dialog and st.session_state.edit_campaign_id:
    campaign = get_campaign_by_id(st.session_state.edit_campaign_id)
    
    if campaign:
        with st.form("edit_campaign_form"):
            st.subheader(f"{ICONS['edit']} Edit Campaign: {campaign['name']}")
            
            name = st.text_input("Campaign Name*", value=campaign['name'])
            description = st.text_area("Description*", value=campaign['description'] or "")
            
            col1, col2 = st.columns(2)
            with col1:
                current_start = campaign['start_date'].date() if hasattr(campaign['start_date'], 'date') else campaign['start_date']
                start_date = st.date_input("Start Date*", value=current_start)
            with col2:
                current_end = campaign['end_date'].date() if campaign['end_date'] and hasattr(campaign['end_date'], 'date') else campaign['end_date']
                end_date = st.date_input("End Date", value=current_end)
            
            is_active = st.checkbox("Active Campaign", value=campaign['is_active'])
            comment = st.text_area("Additional Comments (optional)", value=campaign['comment'] or "")
            
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("Update Campaign", type="primary", use_container_width=True)
            with col_cancel:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)
            
            if submitted:
                if not name or not description:
                    st.error(f"{ICONS['error']} Please fill in all required fields (marked with *)")
                else:
                    # Convert dates to datetime
                    start_datetime = datetime.combine(start_date, datetime.min.time())
                    end_datetime = datetime.combine(end_date, datetime.min.time()) if end_date else None
                    
                    success = update_campaign(
                        campaign_id=st.session_state.edit_campaign_id,
                        name=name,
                        description=description,
                        start_date=start_datetime,
                        end_date=end_datetime,
                        is_active=is_active,
                        comment=comment if comment else None
                    )
                    
                    if success:
                        st.success(f"{ICONS['check']} Campaign '{name}' updated successfully!")
                        st.session_state.show_edit_dialog = False
                        st.session_state.edit_campaign_id = None
                        st.rerun()
                    else:
                        st.error(f"{ICONS['error']} Failed to update campaign.")
            
            if cancelled:
                st.session_state.show_edit_dialog = False
                st.session_state.edit_campaign_id = None
                st.rerun()

# View Campaign Details Dialog
elif st.session_state.show_view_dialog and st.session_state.view_campaign_id:
    campaign = get_campaign_by_id(st.session_state.view_campaign_id)
    
    if campaign:
        st.subheader(f"{ICONS['view']} Campaign Details: {campaign['name']}")
        
        col1, col2 = st.columns(2)
        with col1:
            status_icon = ICONS['active'] if campaign['is_active'] else ICONS['inactive']
            status_text = "Active" if campaign['is_active'] else "Inactive"
            st.write(f"**Status:** {status_icon} {status_text}")
            st.write(f"**Start Date:** {campaign['start_date'].strftime('%Y-%m-%d')}")
            if campaign['end_date']:
                st.write(f"**End Date:** {campaign['end_date'].strftime('%Y-%m-%d')}")
        with col2:
            st.write(f"**Completed:** {campaign['completed']} / {campaign['total']}")
            completion_pct = (campaign['completed'] / campaign['total'] * 100) if campaign['total'] > 0 else 0
            st.progress(completion_pct / 100, text=f"Progress: {completion_pct:.0f}%")
        
        st.write(f"**Description:** {campaign['description']}")
        if campaign['comment']:
            st.write(f"**Comments:** {campaign['comment']}")
        
        # Show evaluations
        st.write("---")
        st.write("**Evaluations:**")
        evaluations = get_campaign_evaluations(st.session_state.view_campaign_id)
        
        if evaluations:
            for eval in evaluations:
                status_icon = {"todo": ICONS['pause'], "pending": ICONS['pending'], "completed": ICONS['check']}.get(eval['status'], ICONS['help'])
                st.write(f"{status_icon} {eval['evaluator_name']} → {eval['evaluatee_name']} ({eval['status']})")
        else:
            st.info("No evaluations found for this campaign.")
        
        if st.button("Close", use_container_width=True):
            st.session_state.show_view_dialog = False
            st.session_state.view_campaign_id = None
            st.rerun()

# Team Assignment Dialog
elif st.session_state.show_team_assignment and st.session_state.team_campaign_id:
    campaign = get_campaign_by_id(st.session_state.team_campaign_id)
    
    if campaign:
        st.subheader(f"{ICONS['teams']} Team Assignment: {campaign['name']}")
        
        # Get all groups and assigned groups
        all_groups = get_all_groups()
        assigned_groups = get_campaign_groups(st.session_state.team_campaign_id)
        assigned_group_ids = [g['id'] for g in assigned_groups]
        
        st.write("**Assigned Teams:**")
        if assigned_groups:
            for group in assigned_groups:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"{ICONS['office']} **{group['name']}**")
                with col2:
                    if st.button(f"{ICONS['matrix']} Matrix", key=f"matrix_{group['id']}", use_container_width=True):
                        st.session_state.show_evaluation_matrix = True
                        st.session_state.matrix_campaign_id = st.session_state.team_campaign_id
                        st.session_state.matrix_group_id = group['id']
                        st.session_state.show_team_assignment = False
                        st.rerun()
                with col3:
                    if st.button(ICONS['close'], key=f"remove_{group['id']}", use_container_width=True):
                        remove_group_from_campaign(st.session_state.team_campaign_id, group['id'])
                        st.rerun()
        else:
            st.info("No teams assigned yet.")
        
        st.write("---")
        st.write("**Available Teams:**")
        unassigned_groups = [g for g in all_groups if g['id'] not in assigned_group_ids]
        
        if unassigned_groups:
            for group in unassigned_groups:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{ICONS['office']} {group['name']}")
                with col2:
                    if st.button(f"{ICONS['add']} Add", key=f"add_{group['id']}", use_container_width=True):
                        assign_group_to_campaign(st.session_state.team_campaign_id, group['id'])
                        st.rerun()
        else:
            st.info("All teams are already assigned.")
        
        if st.button("Close", use_container_width=True):
            st.session_state.show_team_assignment = False
            st.session_state.team_campaign_id = None
            st.rerun()

# Evaluation Matrix Dialog
elif st.session_state.show_evaluation_matrix and st.session_state.matrix_campaign_id and st.session_state.matrix_group_id:
    campaign = get_campaign_by_id(st.session_state.matrix_campaign_id)
    members = get_group_members(st.session_state.matrix_group_id)
    evaluation_matrix = get_campaign_group_evaluations(st.session_state.matrix_campaign_id, st.session_state.matrix_group_id)
    
    # Initialize matrix selections in session state if not exists
    matrix_key = f"matrix_selections_{st.session_state.matrix_campaign_id}_{st.session_state.matrix_group_id}"
    if matrix_key not in st.session_state:
        # Initialize with current selections from database
        st.session_state[matrix_key] = set()
        for evaluator_id in evaluation_matrix:
            for evaluatee_id in evaluation_matrix[evaluator_id]:
                st.session_state[matrix_key].add((evaluator_id, evaluatee_id))
    
    if campaign and members:
        group_info = [g for g in get_all_groups() if g['id'] == st.session_state.matrix_group_id]
        group_name = group_info[0]['name'] if group_info else "Unknown"
        
        st.subheader(f"{ICONS['matrix']} Evaluation Matrix: {campaign['name']} - {group_name}")
        st.write("**Who evaluates whom**")
        st.caption("Rows = Evaluatee (who receives feedback), Columns = Evaluator (who gives feedback)")
        
        # Form selection
        st.write("---")
        st.write("**Select Evaluation Form:**")
        forms = get_all_forms()
        
        if not forms:
            st.error(f"{ICONS['error']} No forms available. Please create an evaluation form first.")
        else:
            form_options = {f"{form['name']}": form['id'] for form in forms}
            selected_form_name = st.selectbox(
                "Form to use for this team*",
                options=list(form_options.keys()),
                key="selected_form"
            )
            selected_form_id = form_options[selected_form_name]
            
            st.write("---")
            
            # Display matrix with checkboxes using data_editor for scrolling
            st.write("**Manual Selection (Evaluatee ↓ / Evaluator →):**")
            st.caption("Check the box where row person is evaluated by column person")
            
            # Create DataFrame for the matrix
            matrix_data = {}
            for evaluator in members:
                evaluator_name = evaluator['name']
                matrix_data[evaluator_name] = []
                
                for evaluatee in members:
                    evaluator_id = evaluator['id']
                    evaluatee_id = evaluatee['id']
                    is_selected = (evaluator_id, evaluatee_id) in st.session_state[matrix_key]
                    matrix_data[evaluator_name].append(is_selected)
            
            # Create DataFrame with evaluatee names as index
            df = pd.DataFrame(matrix_data, index=[m['name'] for m in members])
            
            # Display editable dataframe with scrolling
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                height=min(600, 100 + len(members) * 35),
                hide_index=False,
                key=f"matrix_editor_{matrix_key}"
            )
            
            # Update session state based on edited dataframe
            st.session_state[matrix_key] = set()
            for evaluatee_idx, evaluatee in enumerate(members):
                for evaluator_idx, evaluator in enumerate(members):
                    evaluator_name = evaluator['name']
                    if edited_df.iloc[evaluatee_idx][evaluator_name]:
                        st.session_state[matrix_key].add((evaluator['id'], evaluatee['id']))
            
            st.write("---")
            
            # Auto-assignment controls
            st.write("**Quick Selection:**")
            
            # Store percentage in session state if it doesn't exist
            percentage_key = f"percentage_{st.session_state.matrix_campaign_id}_{st.session_state.matrix_group_id}"
            if percentage_key not in st.session_state:
                st.session_state[percentage_key] = 1
            
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if st.button(f"{ICONS['select_all']} Select All", use_container_width=True):
                    # Select everyone evaluates everyone
                    st.session_state[matrix_key] = set()
                    for evaluator in members:
                        for evaluatee in members:
                            st.session_state[matrix_key].add((evaluator['id'], evaluatee['id']))
                    st.rerun()
            
            with col2:
                if st.button(f"{ICONS['delete']} Clear All", use_container_width=True):
                    # Clear all selections in session state
                    st.session_state[matrix_key] = set()
                    st.rerun()
            
            with col3:
                # Percentage input as number_input button-style
                #TODO: rename percentage_key since it is no longer a percentage
                percentage = st.number_input(
                    "Number of evaluations per Employee",
                    min_value=0,
                    max_value=len(members)-1,
                    value=st.session_state[percentage_key],
                    step=1,
                    key=f"percentage_input_{percentage_key}"
                )
                st.session_state[percentage_key] = percentage
            
            with col4:
                if st.button(f"{ICONS['dice']} Auto-Assign", type="primary", use_container_width=True):
                    st.session_state[matrix_key] = set()

                    ids = [m["id"] for m in members]
                    k = int(percentage)  # minden evaluatee ennyit kap

                    out = {i: 0 for i in ids}  # ki mennyit ad eddig
                    pool = [evaluatee for evaluatee in ids for _ in range(k)]  # mindenkinek k bejövő
                    random.shuffle(pool)

                    for evaluatee in pool:
                        # válassz evaluatort, aki nem önmaga és eddig a legkevesebbet adott
                        candidates = [evaluator for evaluator in ids if
                                      evaluator != evaluatee and (evaluator, evaluatee) not in st.session_state[
                                          matrix_key]]
                        if not candidates:
                            continue

                        min_out = min(out[e] for e in candidates)
                        best = [e for e in candidates if out[e] == min_out]
                        evaluator = random.choice(best)

                        st.session_state[matrix_key].add((evaluator, evaluatee))
                        out[evaluator] += 1

                    st.rerun()
            
            st.write("---")
            
            # Save and Back buttons
            col_save, col_back = st.columns(2)
            with col_save:
                if st.button(f"{ICONS['save']} Save Evaluations", type="primary", use_container_width=True):
                    # Convert session state selections to list of tuples
                    assignments = list(st.session_state[matrix_key])
                    
                    success = save_evaluations_batch(
                        st.session_state.matrix_campaign_id,
                        st.session_state.matrix_group_id,
                        assignments,
                        selected_form_id
                    )
                    
                    if success:
                        st.success(f"{ICONS['check']} Saved {len(assignments)} evaluation assignments with form '{selected_form_name}'!")
                        # Clear session state for this matrix
                        del st.session_state[matrix_key]
                        st.rerun()
                    else:
                        st.error(f"{ICONS['error']} Failed to save evaluations.")
            
            with col_back:
                if st.button("Back to Teams", use_container_width=True):
                    # Clear session state for this matrix
                    if matrix_key in st.session_state:
                        del st.session_state[matrix_key]
                    st.session_state.show_evaluation_matrix = False
                    st.session_state.show_team_assignment = True
                    st.session_state.matrix_group_id = None
                    st.rerun()

# Delete Confirmation Dialog
elif st.session_state.show_delete_confirm and st.session_state.delete_campaign_id:
    campaign = get_campaign_by_id(st.session_state.delete_campaign_id)
    
    if campaign:
        st.warning(f"{ICONS['warning']} Are you sure you want to delete campaign '{campaign['name']}'?")
        st.write("This will also delete all associated evaluations. This action cannot be undone.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete", type="primary", use_container_width=True):
                success = delete_campaign(st.session_state.delete_campaign_id)
                if success:
                    st.success(f"{ICONS['check']} Campaign deleted successfully!")
                    st.session_state.show_delete_confirm = False
                    st.session_state.delete_campaign_id = None
                    st.rerun()
                else:
                    st.error(f"{ICONS['error']} Failed to delete campaign.")
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_delete_confirm = False
                st.session_state.delete_campaign_id = None
                st.rerun()

# Main campaign list view
else:
    # Create New Campaign Button
    st.write("")
    if st.button(f"{ICONS['add']} Create New Campaign", type="primary", use_container_width=True):
        query_params["create"] = "true"
        st.rerun()
    
    st.write("")
    st.write("---")
    st.subheader("Campaign List")
    
    # Fetch campaigns from database
    campaigns = get_all_campaigns()
    
    if not campaigns:
        st.info(f"{ICONS['list']} No campaigns found. Create your first campaign to get started!")
    else:
        # Display campaigns
        for campaign in campaigns:
            # Calculate completion percentage
            completion_pct = (campaign['completed'] / campaign['total'] * 100) if campaign['total'] > 0 else 0
            
            # Status badge icon
            status_icon = ICONS['active'] if campaign['is_active'] else ICONS['inactive']
            status_text = "ACTIVE" if campaign['is_active'] else "INACTIVE"
            
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"### {campaign['name']}")
                    start_str = campaign['start_date'].strftime('%Y-%m-%d')
                    end_str = campaign['end_date'].strftime('%Y-%m-%d') if campaign['end_date'] else "N/A"
                    st.caption(f"Start: {start_str} | End: {end_str}")
                
                with col2:
                    st.write("")
                    st.write(f"{status_icon} **{status_text}**")
                
                with col3:
                    st.write("")
                    st.write(f"**{campaign['completed']}/{campaign['total']}**")
                
                # Progress bar
                st.progress(completion_pct / 100, text=f"Completion: {completion_pct:.0f}%")
                
                # Action buttons
                col_view, col_edit, col_teams, col_toggle, col_delete = st.columns([1, 1, 1, 1, 1])
                
                with col_view:
                    if st.button(f"{ICONS['view']} View", key=f"view_{campaign['id']}", use_container_width=True):
                        st.session_state.show_view_dialog = True
                        st.session_state.view_campaign_id = campaign['id']
                        st.rerun()
                
                with col_edit:
                    if campaign['is_active']:
                        if st.button(f"{ICONS['edit']} Edit", key=f"edit_{campaign['id']}", use_container_width=True):
                            st.session_state.show_edit_dialog = True
                            st.session_state.edit_campaign_id = campaign['id']
                            st.rerun()
                    else:
                        st.button(f"{ICONS['edit']} Edit", key=f"edit_{campaign['id']}", disabled=True, use_container_width=True)
                
                with col_teams:
                    if st.button(f"{ICONS['teams']} Teams", key=f"teams_{campaign['id']}", use_container_width=True):
                        st.session_state.show_team_assignment = True
                        st.session_state.team_campaign_id = campaign['id']
                        st.rerun()
                
                with col_toggle:
                    toggle_icon = ICONS['pause'] if campaign['is_active'] else ICONS['play']
                    toggle_label = f"{toggle_icon} Deactivate" if campaign['is_active'] else f"{toggle_icon} Activate"
                    if st.button(toggle_label, key=f"toggle_{campaign['id']}", use_container_width=True):
                        success = toggle_campaign_status(campaign['id'])
                        if success:
                            st.rerun()
                
                with col_delete:
                    if st.button(f"{ICONS['delete']} Delete", key=f"delete_{campaign['id']}", use_container_width=True):
                        st.session_state.show_delete_confirm = True
                        st.session_state.delete_campaign_id = campaign['id']
                        st.rerun()
                
                st.write("---")

st.write("")
st.info(f"{ICONS['lightbulb']} **Tip:** Use the Teams button to assign groups and configure evaluation matrices for each campaign.")
