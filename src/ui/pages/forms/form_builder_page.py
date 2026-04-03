import streamlit as st
import pandas as pd
from io import BytesIO
from services.form_builder_service import (
    FormBuilderService,
    QUESTION_TYPES,
    new_section,
    new_question,
)

st.markdown(
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0"/>',
    unsafe_allow_html=True,
)

st.title(":material/assignment: Form Builder")
st.write("Create and manage performance evaluation forms with sections and questions.")

svc = FormBuilderService()


def _legacy_multi_import(uploaded_file) -> list[int]:
    uploaded_file.seek(0)
    df = pd.read_excel(uploaded_file, sheet_name="form_questions")
    if "Form Name" not in df.columns:
        raise ValueError("Missing column: Form Name")

    cleaned_df = df.dropna(how="all")
    form_names = []
    for raw_name in cleaned_df["Form Name"].tolist():
        name = str(raw_name).strip() if pd.notna(raw_name) else ""
        if name and name not in form_names:
            form_names.append(name)

    if not form_names:
        raise ValueError("Form Name is required.")

    created_ids = []
    for form_name in form_names:
        form_subset = cleaned_df[cleaned_df["Form Name"].astype(str).str.strip() == form_name]
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            form_subset.to_excel(writer, index=False, sheet_name="form_questions")
        buffer.seek(0)
        created_ids.append(svc.import_form_from_excel(buffer))

    return created_ids

if "fb_current_form_id" not in st.session_state:
    st.session_state.fb_current_form_id = None

st.divider()
tab_list, tab_new = st.tabs([":material/assignment: My Forms", ":material/add: New Form"])

# -------------------------
# NEW FORM
# -------------------------
with tab_new:
    st.subheader("Create New Form")
    with st.form("fb_create_form"):
        nf_title = st.text_input("Form title *", placeholder="e.g., Q1 2024 Performance Review")
        nf_desc = st.text_area("Description", placeholder="Describe the purpose of this form…")

        if st.form_submit_button("Create Form", type="primary"):
            if not nf_title.strip():
                st.error("Please enter a form title.")
            else:
                try:
                    fid = svc.create_form(nf_title.strip(), nf_desc.strip())
                    st.success(f"Form **{nf_title}** created!")
                    st.session_state.fb_current_form_id = fid
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating form: {e}")

    st.divider()
    st.subheader("Import Form from Excel")
    st.caption("Download the template, fill it out, then upload it to create a new form.")

    template_bytes = svc.get_form_import_template_bytes()
    st.download_button(
        "Download form import template",
        data=template_bytes,
        file_name="form_import_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        icon=":material/download:",
        use_container_width=True,
    )

    import_file = st.file_uploader(
        "Upload completed form template (.xlsx)",
        type=["xlsx"],
        key="fb_form_import_file",
    )

    if st.button(
        "Import form from Excel",
        type="primary",
        icon=":material/upload_file:",
        use_container_width=True,
    ):
        if import_file is None:
            st.error("Please upload an .xlsx file first.")
        else:
            try:
                if hasattr(svc, "import_forms_from_excel"):
                    imported_form_ids = svc.import_forms_from_excel(import_file)
                else:
                    imported_form_ids = _legacy_multi_import(import_file)
                st.success(f"{len(imported_form_ids)} form(s) imported successfully.")
                st.session_state.fb_current_form_id = imported_form_ids[-1]
                st.rerun()
            except Exception as e:
                if "Only one Form Name is allowed per uploaded file" in str(e):
                    try:
                        imported_form_ids = _legacy_multi_import(import_file)
                        st.success(f"{len(imported_form_ids)} form(s) imported successfully.")
                        st.session_state.fb_current_form_id = imported_form_ids[-1]
                        st.rerun()
                    except Exception as fallback_error:
                        st.error(f"Error importing form: {fallback_error}")
                else:
                    st.error(f"Error importing form: {e}")

# -------------------------
# LIST + EDIT
# -------------------------
with tab_list:
    all_forms = svc.list_forms()

    if not all_forms:
        st.info("No forms yet. Switch to **➕ New Form** to create one.")
        st.stop()

    form_options = {f"{f.name}": f.id for f in all_forms}

    default_idx = 0
    if st.session_state.fb_current_form_id in form_options.values():
        default_idx = list(form_options.values()).index(st.session_state.fb_current_form_id)

    selected_key = st.selectbox("Select form to edit:", list(form_options.keys()), index=default_idx)
    selected_id = form_options[selected_key]
    st.session_state.fb_current_form_id = selected_id

    form_row = svc.get_form(selected_id)
    if not form_row:
        st.error("Could not load the selected form.")
        st.stop()

    form_id = form_row.id
    form_name = form_row.name
    form_desc = form_row.description
    content = svc.migrate_content(form_row.questions)
    sections = content.get("sections", [])

    # Header card
    with st.container(border=True):
        hcol1, hcol2 = st.columns([12, 1])
        with hcol1:
            st.markdown(f"## {form_name}")
            if form_desc:
                st.caption(form_desc)
            total_q = sum(len(s.get("questions", [])) for s in sections)
            st.caption(f"**{total_q}** question(s) across **{len(sections)}** section(s)")
        with hcol2:
            st.write("")  # spacer — a gombot a cím mellé igazítja
            if st.button("", icon=":material/delete:", key=f"del_form_{form_id}"):
                try:
                    svc.delete_form(form_id)
                    st.session_state.fb_current_form_id = None
                    st.success("Form deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting form: {e}")

    st.write("")

    # Sections loop
    for sec_idx, section in enumerate(sections):
        sec_title = section.get("title", f"Section {sec_idx + 1}")
        questions = section.get("questions", [])

        with st.container(border=True):
            sec_head_col, sec_ctrl2 = st.columns([12, 2])
            with sec_head_col:
                st.markdown(
                    f"""<div style="background:#f8fafc;color:#0f172a;padding:8px 14px;
                    border-left:3px solid #cbd5e1;border-radius:6px;font-weight:600;font-size:1.05rem;margin-bottom:10px;
                    display:flex;align-items:center;gap:8px">
                    <span class="material-symbols-outlined" style="font-size:1.2rem;font-weight:400;line-height:1">folder</span>
                    {sec_title}</div>""",
                    unsafe_allow_html=True,
                )

            rename_key = f"show_rename_sec_{form_id}_{sec_idx}"
            add_q_key = f"show_add_q_{form_id}_{sec_idx}"
            with sec_ctrl2:
                acol, rcol, dcol = st.columns([1, 1, 1])
                with acol:
                    if st.button(
                            "",
                            icon=":material/add:",
                            key=f"add_q_btn_{form_id}_{sec_idx}",
                            help="Add question",
                    ):
                        st.session_state[add_q_key] = not st.session_state.get(add_q_key, False)
                with rcol:
                    if st.button(
                            "",
                            icon=":material/edit:",
                            key=f"rename_btn_{form_id}_{sec_idx}",
                            help="Rename section",
                    ):
                        st.session_state[rename_key] = not st.session_state.get(rename_key, False)
                with dcol:
                    if st.button(
                            "",
                            icon=":material/delete:",
                            key=f"del_sec_{form_id}_{sec_idx}",
                            help="Delete this section and all its questions",
                    ):
                        sections.pop(sec_idx)
                        content["sections"] = sections
                        try:
                            svc.save_content(form_id, content)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving form: {e}")

            if st.session_state.get(rename_key, False):
                with st.form(f"fb_rename_sec_{form_id}_{sec_idx}"):
                    new_sec_name = st.text_input(
                        "New section name",
                        value=sec_title,
                        label_visibility="collapsed",
                    )
                    if st.form_submit_button("Rename"):
                        if new_sec_name.strip():
                            sections[sec_idx]["title"] = new_sec_name.strip()
                            content["sections"] = sections
                            try:
                                svc.save_content(form_id, content)
                                st.session_state[rename_key] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saving form: {e}")

            st.divider()

            # Questions list
            if not questions:
                st.caption("_No questions yet in this section._")
            else:
                for q_idx, q in enumerate(questions):
                    qtype = q.get("type", "text")
                    type_icon, type_label = QUESTION_TYPES.get(qtype, (":material/help:", "Unknown"))
                    req_star = " \\*" if q.get("required") else ""

                    qcol1, qcol2 = st.columns([10, 1])
                    with qcol1:
                        st.markdown(f"{type_icon} **{q.get('text','')}{req_star}**")
                        st.caption(f"_{type_label}_")

                        if qtype == "multiple_choice" and q.get("options"):
                            for opt in q["options"]:
                                st.write(f"&nbsp;&nbsp;○ {opt}")
                        elif qtype == "rating":
                            lo = int(q.get("rating_min", 1))
                            hi = int(q.get("rating_max", 5))
                            st.markdown(
                                "<div style='display:flex;gap:6px;margin:4px 0'>"
                                + "".join(
                                    f"<span style='background:#f0f2f6;border-radius:50%;width:30px;"
                                    f"height:30px;display:flex;align-items:center;justify-content:center;"
                                    f"font-size:0.85rem'>{i}</span>"
                                    for i in range(lo, hi + 1)
                                )
                                + "</div>",
                                unsafe_allow_html=True,
                            )
                        elif qtype == "slider_labels" and q.get("slider_options"):
                            options = q["slider_options"]
                            st.markdown(
                                "<div style='display:flex;gap:6px;margin:4px 0'>"
                                + "".join(
                                    f"<span style='background:#e8f4f8;border-radius:8px;padding:4px 8px;"
                                    f"font-size:0.8rem'>{opt}</span>"
                                    for opt in options
                                )
                                + "</div>",
                                unsafe_allow_html=True,
                            )

                    with qcol2:
                        if st.button("", icon=":material/delete:", key=f"del_q_{form_id}_{sec_idx}_{q_idx}", help="Delete question"):
                            sections[sec_idx]["questions"].pop(q_idx)
                            content["sections"] = sections
                            try:
                                svc.save_content(form_id, content)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saving form: {e}")

                    st.write("")

            # Add question panel (toggled by + icon)
            if st.session_state.get(add_q_key, False):
                ss_key = f"fb_qtype_{form_id}_{sec_idx}"
                if ss_key not in st.session_state:
                    st.session_state[ss_key] = "text"

                aq_type = st.selectbox(
                    "Question type",
                    options=list(QUESTION_TYPES.keys()),
                    format_func=lambda t: QUESTION_TYPES[t][1],
                    key=ss_key,
                )

                with st.form(f"fb_add_q_{form_id}_{sec_idx}"):
                    aq_text = st.text_input("Question text *", placeholder="Type your question here…")
                    aq_required = st.checkbox("Required", value=True)

                    # type-specific controls
                    if aq_type == "multiple_choice":
                        st.caption("**Options** — one per line:")
                        aq_options_raw = st.text_area(
                            "Options",
                            placeholder="Option A\nOption B\nOption C",
                            label_visibility="collapsed",
                        )
                        aq_rating_min, aq_rating_max, aq_slider_labels_raw = 1, 5, ""
                    elif aq_type == "rating":
                        st.caption("**Scale range:**")
                        rc1, rc2 = st.columns(2)
                        with rc1:
                            aq_rating_min = st.number_input("Min", min_value=0, max_value=9, value=1)
                        with rc2:
                            aq_rating_max = st.number_input("Max", min_value=1, max_value=10, value=5)
                        aq_options_raw, aq_slider_labels_raw = "", ""
                    elif aq_type == "slider_labels":
                        st.caption("**Options** — one per line:")
                        aq_slider_labels_raw = st.text_area(
                            "Options",
                            placeholder="Nagyon jól\nInkább jól\nSemleges\nInkább nem jól\nNem jól",
                            label_visibility="collapsed",
                        )
                        aq_options_raw, aq_rating_min, aq_rating_max = "", 1, 5
                    else:
                        aq_options_raw, aq_rating_min, aq_rating_max, aq_slider_labels_raw = "", 1, 5, ""

                    if st.form_submit_button("Add Question", icon=":material/add:", type="primary"):
                        if not aq_text.strip():
                            st.error("Please enter a question text.")
                        elif aq_type == "multiple_choice" and not aq_options_raw.strip():
                            st.error("Please enter at least one option.")
                        elif aq_type == "rating" and int(aq_rating_min) >= int(aq_rating_max):
                            st.error("Min value must be less than Max value.")
                        elif aq_type == "slider_labels":
                            slider_options = [line.strip() for line in aq_slider_labels_raw.splitlines() if line.strip()]
                            if len(slider_options) < 2:
                                st.error("Please enter at least 2 options.")
                                st.stop()

                            nq = new_question(
                                text=aq_text.strip(),
                                qtype=aq_type,
                                required=aq_required,
                                slider_options=slider_options,
                            )
                            sections[sec_idx]["questions"].append(nq)
                            content["sections"] = sections
                            try:
                                svc.save_content(form_id, content)
                                st.success("Question added!")
                                st.session_state[add_q_key] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saving form: {e}")
                        else:
                            opts = (
                                [o.strip() for o in aq_options_raw.splitlines() if o.strip()]
                                if aq_type == "multiple_choice"
                                else None
                            )
                            nq = new_question(
                                text=aq_text.strip(),
                                qtype=aq_type,
                                required=aq_required,
                                options=opts,
                                rating_min=int(aq_rating_min),
                                rating_max=int(aq_rating_max),
                            )
                            sections[sec_idx]["questions"].append(nq)
                            content["sections"] = sections
                            try:
                                svc.save_content(form_id, content)
                                st.success("Question added!")
                                st.session_state[add_q_key] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saving form: {e}")

        st.write("")

    # Add section
    st.divider()
    with st.form(f"fb_add_sec_{form_id}"):
        ns_col1, ns_col2 = st.columns([4, 1])
        with ns_col1:
            new_sec_title = st.text_input(
                "New section name",
                placeholder="e.g., Leadership Skills",
                label_visibility="collapsed",
            )
        with ns_col2:
            add_sec_btn = st.form_submit_button("Add Section", icon=":material/add:", type="secondary", use_container_width=True)

        if add_sec_btn:
            if not new_sec_title.strip():
                st.error("Please enter a section name.")
            else:
                sections.append(new_section(new_sec_title.strip()))
                content["sections"] = sections
                try:
                    svc.save_content(form_id, content)
                    st.success(f"Section **{new_sec_title}** added!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving form: {e}")

    # Preview
    if sections and any(s.get("questions") for s in sections):
        st.divider()
        with st.expander(":material/visibility: Form Preview", expanded=False):
            st.markdown(f"## {form_name}")
            if form_desc:
                st.write(form_desc)
            st.divider()

            q_global = 1
            for section in sections:
                st.markdown(
                    f"""<div style="background:#f8fafc;color:#0f172a;padding:6px 12px;
                    border-left:3px solid #cbd5e1;border-radius:6px;font-weight:600;margin:12px 0 8px 0;
                    display:flex;align-items:center;gap:8px">
                    <span class="material-symbols-outlined" style="font-size:1.1rem;font-weight:400;line-height:1">folder</span>
                    {section.get('title','Section')}</div>""",
                    unsafe_allow_html=True,
                )
                for q in section.get("questions", []):
                    req_mark = " *" if q.get("required") else ""
                    st.markdown(f"**{q_global}. {q.get('text','')}{req_mark}**")

                    qtype = q.get("type")
                    if qtype == "text":
                        st.text_area("Your answer", key=f"prev_t_{q['id']}", disabled=True, height=90)
                    elif qtype == "multiple_choice":
                        for opt in q.get("options", []):
                            st.write(f"○ {opt}")
                    elif qtype == "rating":
                        lo, hi = int(q.get("rating_min", 1)), int(q.get("rating_max", 5))
                        st.slider(
                            "Rating",
                            min_value=lo,
                            max_value=hi,
                            value=lo,
                            key=f"prev_r_{q['id']}",
                            disabled=True,
                        )
                    elif qtype == "slider_labels":
                        options = q.get("slider_options", [])
                        if options:
                            st.select_slider(
                                "Select value",
                                options=options,
                                value=options[0],
                                key=f"prev_sl_{q['id']}",
                                disabled=True,
                            )
                    st.write("")
                    q_global += 1



                    st.write("")
                    q_global += 1




