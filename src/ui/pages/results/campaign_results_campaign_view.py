import io
from datetime import datetime

import pandas as pd
import streamlit as st


NO_CAMPAIGN_SELECTED = "-- Select a campaign --"


def get_selected_campaign_index(campaign_options):
    selected_campaign_name = st.session_state.cr_selected_campaign_name
    if selected_campaign_name and selected_campaign_name in campaign_options:
        return campaign_options.index(selected_campaign_name)
    return 0


def load_campaign_metrics(campaign_results_service, participants_df, campaign_id):
    total_completed = campaign_results_service.count_completed_evaluations_for_campaign(campaign_id)
    participant_count = int(len(participants_df))
    participants_with_feedback = int((participants_df["completed_evaluations"] > 0).sum()) if participant_count else 0
    participation_rate = (participants_with_feedback / participant_count * 100) if participant_count else 0.0

    return participant_count, total_completed, participants_with_feedback, participation_rate


def render_campaign_metrics(participant_count, total_completed, participants_with_feedback, participation_rate):
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Participants", participant_count)
    k2.metric("Completed Evaluations", total_completed)
    k3.metric("Participants with Feedback", participants_with_feedback)
    k4.metric("Coverage", f"{participation_rate:.0f}%")

    if total_completed < 3:
        st.warning("Low data quality: too few completed evaluations for reliable campaign-level insight.")


def render_participant_filters(participants_df, participant_count):
    with st.container(border=True):
        st.caption("Filters")
        f1, f2 = st.columns([2.5, 1.5])
        with f1:
            search_name = st.text_input(
                "Search participant",
                key="cr_filter_search_name",
                placeholder="Type name or email...",
            ).strip().lower()

        roles = sorted(participants_df["role"].fillna("No role").astype(str).unique().tolist()) if participant_count else []
        with f2:
            selected_roles = st.multiselect(
                "Role",
                options=roles,
                default=[],
                key="cr_filter_roles",
                placeholder="Select role(s)...",
            )

        f3, f4 = st.columns([3.0, 1.0])
        with f3:
            max_completed = int(participants_df["completed_evaluations"].max()) if participant_count else 0
            if max_completed <= 0:
                min_completed = st.slider(
                    "Minimum completed evaluations",
                    min_value=0,
                    max_value=1,
                    value=0,
                    key="cr_filter_min_completed",
                    disabled=True,
                )
            else:
                min_completed = st.slider(
                    "Minimum completed evaluations",
                    min_value=0,
                    max_value=max_completed,
                    value=0,
                    key="cr_filter_min_completed",
                )

        with f4:
            st.write("")
            reset = st.button("Reset filters", key="cr_reset_filters", use_container_width=True)

        if reset:
            st.session_state.cr_filter_search_name = ""
            st.session_state.cr_filter_roles = []
            st.session_state.cr_filter_min_completed = 0
            st.rerun()

    return search_name, selected_roles, min_completed


def filter_participants(participants_df, participant_count, search_name, selected_roles, min_completed):
    filtered_df = participants_df.copy()
    if participant_count:
        if search_name:
            filtered_df = filtered_df[
                filtered_df["name"].str.lower().str.contains(search_name, na=False)
                | filtered_df["email"].fillna("").str.lower().str.contains(search_name, na=False)
            ]
        if selected_roles:
            filtered_df = filtered_df[filtered_df["role"].isin(selected_roles)]
        filtered_df = filtered_df[filtered_df["completed_evaluations"] >= int(min_completed)]

    return filtered_df


def build_filter_chips(search_name, selected_roles, min_completed):
    chips = []
    if search_name:
        chips.append(f"search: {search_name}")
    if selected_roles:
        chips.append(f"roles: {', '.join(selected_roles)}")
    if int(min_completed) > 0:
        chips.append(f"min completed: {int(min_completed)}")

    return chips


def build_participants_export(filtered_df, selected_campaign, chips):
    if filtered_df.empty:
        return None

    csv_df = filtered_df.copy()
    csv_df["campaign_name"] = selected_campaign
    csv_df["generated_at"] = datetime.utcnow().isoformat()
    csv_df["active_filters"] = "; ".join(chips) if chips else "none"
    export_df = csv_df.rename(
        columns={
            "completed_evaluations": "completed evaluations",
            "campaign_name": "campaign",
            "generated_at": "generated at",
            "active_filters": "active filters",
        }
    )
    export_buffer = io.BytesIO()
    with pd.ExcelWriter(export_buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Participants")

    return export_buffer.getvalue()


def render_participants_export(export_xlsx_bytes, campaign_id):
    with st.container(border=True):
        st.caption("Export")
        st.download_button(
            ":material/download: Export participants (Excel)",
            data=export_xlsx_bytes if export_xlsx_bytes is not None else b"",
            file_name=f"campaign_participants_{campaign_id}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="cr_export_participants_xlsx",
            use_container_width=True,
            disabled=(export_xlsx_bytes is None),
            type="secondary",
        )


def render_participants_table(filtered_df):
    preview_df = filtered_df[["name", "email", "role", "completed_evaluations"]].copy()
    preview_df = preview_df.sort_values(by=["completed_evaluations", "name"], ascending=[False, True])
    preview_df = preview_df.rename(
        columns={
            "name": "Name",
            "email": "Email",
            "role": "Role",
            "completed_evaluations": "Completed evaluations",
        }
    )
    st.dataframe(preview_df, use_container_width=True, hide_index=True)


def render_campaign_navigation():
    with st.container(border=True):
        st.caption("Navigation")
        if st.button(
            ":material/assessment: Overall Results",
            key="btn_overall_summary",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.cr_view = "overall"
            st.rerun()


def render_employee_cards(filtered_df):
    employees = filtered_df.to_dict("records")
    for emp in employees:
        with st.container(border=True):
            col_name, col_role, col_arrow = st.columns([3, 1, 1])
            with col_name:
                st.markdown(f"**{emp['name']}**")
                st.caption(emp.get("email") or "")
            with col_role:
                st.caption(emp["role"] if emp["role"] else "No role")
                st.caption(f"Completed: {int(emp.get('completed_evaluations', 0))}")
            with col_arrow:
                if st.button("→", key=f"btn_{emp['id']}"):
                    st.session_state.cr_view = "employee"
                    st.session_state.cr_selected_employee_id = emp["id"]
                    st.session_state.cr_selected_employee_name = emp["name"]
                    st.rerun()


def render_campaign_details(db, campaign_results_service, campaign_id, selected_campaign):
    st.session_state.cr_selected_campaign_id = campaign_id
    st.session_state.cr_selected_campaign_name = selected_campaign

    participants_df = campaign_results_service.get_participants_df_for_campaign(campaign_id)
    participant_count, total_completed, participants_with_feedback, participation_rate = load_campaign_metrics(
        campaign_results_service,
        participants_df,
        campaign_id,
    )
    render_campaign_metrics(participant_count, total_completed, participants_with_feedback, participation_rate)

    st.divider()
    search_name, selected_roles, min_completed = render_participant_filters(participants_df, participant_count)
    filtered_df = filter_participants(participants_df, participant_count, search_name, selected_roles, min_completed)
    chips = build_filter_chips(search_name, selected_roles, min_completed)
    if chips:
        st.caption("Active filters: " + " | ".join(chips))

    export_xlsx_bytes = build_participants_export(filtered_df, selected_campaign, chips)
    render_participants_export(export_xlsx_bytes, campaign_id)

    st.divider()
    if filtered_df.empty:
        st.info("No participants match the selected filters.")
        return

    render_participants_table(filtered_df)
    st.divider()
    render_campaign_navigation()
    st.divider()
    render_employee_cards(filtered_df)


def render_campaign_view(db, campaign_results_service):
    st.title("Campaign Results")
    campaign_options, campaign_dict = campaign_results_service.list_campaign_options(NO_CAMPAIGN_SELECTED)
    current_idx = get_selected_campaign_index(campaign_options)
    selected_campaign = st.selectbox("Select Campaign", campaign_options, index=current_idx)

    if selected_campaign == NO_CAMPAIGN_SELECTED:
        st.session_state.cr_selected_campaign_id = None
        st.session_state.cr_selected_campaign_name = None
        st.info("Please select a campaign to view participants.")
        return

    render_campaign_details(
        db,
        campaign_results_service,
        campaign_dict[selected_campaign],
        selected_campaign,
    )
