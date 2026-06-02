import streamlit as st
import streamlit.components.v1 as components

from services.form_builder_service import (
    FormBuilderService,
    QUESTION_TYPES,
    new_question,
    new_section,
)
from ui.pages.forms.form_builder_styles import (
    MATERIAL_SYMBOLS_CSS,
    rating_scale_html,
    scroll_to_anchor_script,
    section_header_html,
    slider_options_html,
)


svc = FormBuilderService()


def init_page() -> None:
    st.markdown(MATERIAL_SYMBOLS_CSS, unsafe_allow_html=True)
    st.title(":material/assignment: Create & Edit Forms")
    st.write("Create and manage performance evaluation forms with sections and questions.")

    if "fb_current_form_id" not in st.session_state:
        st.session_state.fb_current_form_id = None


def ui_key(*parts: object) -> str:
    return "_".join(str(part) for part in parts)


def section_state_key(name: str, form_id: int, section_idx: int) -> str:
    return ui_key(name, form_id, section_idx)


def question_type_key(form_id: int, section_idx: int) -> str:
    return ui_key("fb_qtype", form_id, section_idx)


def add_question_anchor_id(form_id: int, section_idx: int) -> str:
    return ui_key("add_q_anchor", form_id, section_idx)


def save_content_and_rerun(form_id: int, content: dict, sections: list[dict], success_message: str | None = None) -> None:
    content["sections"] = sections
    try:
        svc.save_content(form_id, content)
        if success_message:
            st.success(success_message)
        st.rerun()
    except Exception as e:
        st.error(f"Error saving form: {e}")


def render_section_header(title: str, preview: bool = False) -> None:
    st.markdown(section_header_html(title, preview), unsafe_allow_html=True)


def render_create_form_panel() -> None:
    st.subheader("Create New Form")
    with st.form("fb_create_form"):
        nf_title = st.text_input("Form title *", placeholder="e.g., Q1 2024 Performance Review")
        nf_desc = st.text_area("Description", placeholder="Describe the purpose of this form…")

        if st.form_submit_button("Create Form", type="primary"):
            if not nf_title.strip():
                st.error("Please enter a form title.")
                return

            try:
                fid = svc.create_form(nf_title.strip(), nf_desc.strip())
                st.success(f"Form **{nf_title}** created!")
                st.session_state.fb_current_form_id = fid
                st.rerun()
            except Exception as e:
                st.error(f"Error creating form: {e}")


def render_import_panel() -> None:
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

    if not st.button(
        "Import form from Excel",
        type="primary",
        icon=":material/upload_file:",
        use_container_width=True,
    ):
        return

    if import_file is None:
        st.error("Please upload an .xlsx file first.")
        return

    try:
        imported_form_ids = svc.import_forms_from_excel(import_file)
        st.success(f"{len(imported_form_ids)} form(s) imported successfully.")
        st.session_state.fb_current_form_id = imported_form_ids[-1]
        st.rerun()
    except Exception as e:
        st.error(f"Error importing form: {e}")


def render_new_form_tab() -> None:
    render_create_form_panel()
    render_import_panel()


def render_form_selector(all_forms) -> int:
    form_options = {f"{f.name}": f.id for f in all_forms}

    default_idx = 0
    if st.session_state.fb_current_form_id in form_options.values():
        default_idx = list(form_options.values()).index(st.session_state.fb_current_form_id)

    selected_key = st.selectbox("Select form to edit:", list(form_options.keys()), index=default_idx)
    selected_id = form_options[selected_key]
    st.session_state.fb_current_form_id = selected_id
    return selected_id


def render_form_header(form_id: int, form_name: str, form_desc: str | None, sections: list[dict]) -> None:
    with st.container(border=True):
        hcol1, hcol2 = st.columns([12, 1])
        with hcol1:
            st.markdown(f"## {form_name}")
            if form_desc:
                st.caption(form_desc)
            total_q = sum(len(s.get("questions", [])) for s in sections)
            st.caption(f"**{total_q}** question(s) across **{len(sections)}** section(s)")
        with hcol2:
            st.write("")
            if st.button("", icon=":material/delete:", key=ui_key("del_form", form_id)):
                try:
                    svc.delete_form(form_id)
                    st.session_state.fb_current_form_id = None
                    st.success("Form deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting form: {e}")


def render_question_type_details(q: dict, mode: str) -> None:
    qtype = q.get("type", "text")

    if mode == "preview" and qtype == "text":
        st.text_area("Your answer", key=ui_key("prev_t", q["id"]), disabled=True, height=90)
    elif qtype == "multiple_choice":
        for opt in q.get("options", []):
            st.write(f"{'&nbsp;&nbsp;' if mode == 'editor' else ''}○ {opt}")
    elif qtype == "rating" and mode == "preview":
        lo, hi = int(q.get("rating_min", 1)), int(q.get("rating_max", 5))
        st.slider(
            "Rating",
            min_value=lo,
            max_value=hi,
            value=lo,
            key=ui_key("prev_r", q["id"]),
            disabled=True,
        )
    elif qtype == "rating":
        lo = int(q.get("rating_min", 1))
        hi = int(q.get("rating_max", 5))
        st.markdown(rating_scale_html(lo, hi), unsafe_allow_html=True)
    elif qtype == "slider_labels" and mode == "preview":
        options = q.get("slider_options", [])
        if options:
            st.select_slider(
                "Select value",
                options=options,
                value=options[0],
                key=ui_key("prev_sl", q["id"]),
                disabled=True,
            )
    elif qtype == "slider_labels" and q.get("slider_options"):
        st.markdown(slider_options_html(q["slider_options"]), unsafe_allow_html=True)


def render_question_summary(q: dict) -> None:
    qtype = q.get("type", "text")
    type_icon, type_label = QUESTION_TYPES.get(qtype, (":material/help:", "Unknown"))
    req_star = " \\*" if q.get("required") else ""

    st.markdown(f"{type_icon} **{q.get('text', '')}{req_star}**")
    st.caption(f"_{type_label}_")
    render_question_type_details(q, mode="editor")


def render_question_list(form_id: int, content: dict, sections: list[dict], sec_idx: int, questions: list[dict]) -> None:
    if not questions:
        st.caption("_No questions yet in this section._")
        return

    for q_idx, q in enumerate(questions):
        qcol1, qcol2 = st.columns([10, 1])
        with qcol1:
            render_question_summary(q)

        with qcol2:
            if st.button("", icon=":material/delete:", key=ui_key("del_q", form_id, sec_idx, q_idx), help="Delete question"):
                sections[sec_idx]["questions"].pop(q_idx)
                save_content_and_rerun(form_id, content, sections)

        st.write("")


def render_add_question_type_controls(aq_type: str):
    if aq_type == "multiple_choice":
        st.caption("**Options** — one per line:")
        aq_options_raw = st.text_area(
            "Options",
            placeholder="Option A\nOption B\nOption C",
            label_visibility="collapsed",
        )
        return aq_options_raw, 1, 5, ""

    if aq_type == "rating":
        st.caption("**Scale range:**")
        rc1, rc2 = st.columns(2)
        with rc1:
            aq_rating_min = st.number_input("Min", min_value=0, max_value=9, value=1)
        with rc2:
            aq_rating_max = st.number_input("Max", min_value=1, max_value=10, value=5)
        return "", aq_rating_min, aq_rating_max, ""

    if aq_type == "slider_labels":
        st.caption("**Options** — one per line:")
        aq_slider_labels_raw = st.text_area(
            "Options",
            placeholder="Nagyon jól\nInkább jól\nSemleges\nInkább nem jól\nNem jól",
            label_visibility="collapsed",
        )
        return "", 1, 5, aq_slider_labels_raw

    return "", 1, 5, ""


def build_question_from_form(
    aq_text: str,
    aq_type: str,
    aq_required: bool,
    aq_options_raw: str,
    aq_rating_min: int,
    aq_rating_max: int,
    aq_slider_labels_raw: str,
) -> dict | None:
    if not aq_text.strip():
        st.error("Please enter a question text.")
        return None

    if aq_type == "multiple_choice":
        opts = [o.strip() for o in aq_options_raw.splitlines() if o.strip()]
        if not opts:
            st.error("Please enter at least one option.")
            return None
        return new_question(text=aq_text.strip(), qtype=aq_type, required=aq_required, options=opts)

    if aq_type == "rating":
        if int(aq_rating_min) >= int(aq_rating_max):
            st.error("Min value must be less than Max value.")
            return None
        return new_question(
            text=aq_text.strip(),
            qtype=aq_type,
            required=aq_required,
            rating_min=int(aq_rating_min),
            rating_max=int(aq_rating_max),
        )

    if aq_type == "slider_labels":
        slider_options = [line.strip() for line in aq_slider_labels_raw.splitlines() if line.strip()]
        if len(slider_options) < 2:
            st.error("Please enter at least 2 options.")
            return None
        return new_question(text=aq_text.strip(), qtype=aq_type, required=aq_required, slider_options=slider_options)

    return new_question(text=aq_text.strip(), qtype=aq_type, required=aq_required)


def render_scroll_anchor(anchor_id: str) -> None:
    st.markdown(f"<div id='{anchor_id}'></div>", unsafe_allow_html=True)
    if st.session_state.get("fb_scroll_to") != anchor_id:
        return

    components.html(
        scroll_to_anchor_script(anchor_id),
        height=0,
    )
    st.session_state["fb_scroll_to"] = None


def render_add_question_panel(form_id: int, content: dict, sections: list[dict], sec_idx: int, add_q_key: str) -> None:
    anchor_id = add_question_anchor_id(form_id, sec_idx)
    render_scroll_anchor(anchor_id)

    ss_key = question_type_key(form_id, sec_idx)
    if ss_key not in st.session_state:
        st.session_state[ss_key] = "text"

    aq_type = st.selectbox(
        "Question type",
        options=list(QUESTION_TYPES.keys()),
        format_func=lambda t: QUESTION_TYPES[t][1],
        key=ss_key,
    )

    with st.form(ui_key("fb_add_q", form_id, sec_idx)):
        aq_text = st.text_input("Question text *", placeholder="Type your question here…")
        aq_required = st.checkbox("Required", value=True)
        aq_options_raw, aq_rating_min, aq_rating_max, aq_slider_labels_raw = render_add_question_type_controls(aq_type)

        if not st.form_submit_button("Add Question", icon=":material/add:", type="primary"):
            return

        question = build_question_from_form(
            aq_text=aq_text,
            aq_type=aq_type,
            aq_required=aq_required,
            aq_options_raw=aq_options_raw,
            aq_rating_min=aq_rating_min,
            aq_rating_max=aq_rating_max,
            aq_slider_labels_raw=aq_slider_labels_raw,
        )
        if question is None:
            return

        sections[sec_idx]["questions"].append(question)
        st.session_state[add_q_key] = False
        save_content_and_rerun(form_id, content, sections, "Question added!")


def render_section_controls(form_id: int, content: dict, sections: list[dict], sec_idx: int) -> tuple[str, str, str]:
    rename_key = section_state_key("show_rename_sec", form_id, sec_idx)
    add_q_key = section_state_key("show_add_q", form_id, sec_idx)
    collapse_key = section_state_key("show_questions", form_id, sec_idx)
    if collapse_key not in st.session_state:
        st.session_state[collapse_key] = False

    acol, ccol, rcol, dcol = st.columns([1, 1, 1, 1])
    with acol:
        if st.button("", icon=":material/add:", key=f"add_q_btn_{form_id}_{sec_idx}", help="Add question"):
            st.session_state[add_q_key] = not st.session_state.get(add_q_key, False)
            if st.session_state[add_q_key]:
                st.session_state["fb_scroll_to"] = add_question_anchor_id(form_id, sec_idx)
    with ccol:
        if st.button(
            "",
            icon=":material/keyboard_arrow_down:" if not st.session_state[collapse_key] else ":material/keyboard_arrow_up:",
            key=ui_key("toggle_q_btn", form_id, sec_idx),
            help="Show/Hide questions in this section",
        ):
            st.session_state[collapse_key] = not st.session_state[collapse_key]
            st.rerun()
    with rcol:
        if st.button("", icon=":material/edit:", key=ui_key("rename_btn", form_id, sec_idx), help="Rename section"):
            st.session_state[rename_key] = not st.session_state.get(rename_key, False)
    with dcol:
        if st.button(
            "",
            icon=":material/delete:",
            key=ui_key("del_sec", form_id, sec_idx),
            help="Delete this section and all its questions",
        ):
            sections.pop(sec_idx)
            save_content_and_rerun(form_id, content, sections)

    return rename_key, add_q_key, collapse_key


def render_rename_section_form(form_id: int, content: dict, sections: list[dict], sec_idx: int, sec_title: str, rename_key: str) -> None:
    if not st.session_state.get(rename_key, False):
        return

    with st.form(ui_key("fb_rename_sec", form_id, sec_idx)):
        new_sec_name = st.text_input(
            "New section name",
            value=sec_title,
            label_visibility="collapsed",
        )
        if st.form_submit_button("Rename") and new_sec_name.strip():
            sections[sec_idx]["title"] = new_sec_name.strip()
            st.session_state[rename_key] = False
            save_content_and_rerun(form_id, content, sections)


def render_section_card(form_id: int, content: dict, sections: list[dict], sec_idx: int, section: dict) -> None:
    sec_title = section.get("title", f"Section {sec_idx + 1}")
    questions = section.get("questions", [])

    with st.container(border=True):
        sec_head_col, sec_ctrl_col = st.columns([12, 2])
        with sec_head_col:
            render_section_header(sec_title)

        with sec_ctrl_col:
            rename_key, add_q_key, collapse_key = render_section_controls(form_id, content, sections, sec_idx)

        render_rename_section_form(form_id, content, sections, sec_idx, sec_title, rename_key)

        st.divider()

        if not st.session_state[collapse_key]:
            st.caption("_Section collapsed. Click the expand icon to show questions._")
        else:
            render_question_list(form_id, content, sections, sec_idx, questions)

        if st.session_state.get(add_q_key, False) and st.session_state[collapse_key]:
            render_add_question_panel(form_id, content, sections, sec_idx, add_q_key)


def render_sections(form_id: int, content: dict, sections: list[dict]) -> None:
    for sec_idx, section in enumerate(sections):
        render_section_card(form_id, content, sections, sec_idx, section)
        st.write("")


def render_add_section_form(form_id: int, content: dict, sections: list[dict]) -> None:
    st.divider()
    with st.form(ui_key("fb_add_sec", form_id)):
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
                return

            sections.append(new_section(new_sec_title.strip()))
            save_content_and_rerun(form_id, content, sections, f"Section **{new_sec_title}** added!")


def render_preview_question(q: dict, q_global: int) -> None:
    st.markdown(f"**{q_global}. {q.get('text', '')}**")
    render_question_type_details(q, mode="preview")
    st.write("")


def render_form_preview(form_name: str, form_desc: str | None, sections: list[dict]) -> None:
    if not (sections and any(s.get("questions") for s in sections)):
        return

    st.divider()
    with st.expander(":material/visibility: Form Preview", expanded=False):
        st.markdown(f"## {form_name}")
        if form_desc:
            st.write(form_desc)
        st.divider()

        q_global = 1
        for section in sections:
            render_section_header(section.get("title", "Section"), preview=True)
            for q in section.get("questions", []):
                render_preview_question(q, q_global)
                q_global += 1


def render_forms_list_tab() -> None:
    st.info("Manage your existing forms here. Open a form to review or edit its sections and questions.")
    all_forms = svc.list_forms()

    if not all_forms:
        st.info("No forms yet. Switch to **➕ New Form** to create one.")
        st.stop()

    selected_id = render_form_selector(all_forms)
    form_row = svc.get_form(selected_id)
    if not form_row:
        st.error("Could not load the selected form.")
        st.stop()

    form_id = form_row.id
    form_name = form_row.name
    form_desc = form_row.description
    content = svc.migrate_content(form_row.questions)
    sections = content.get("sections", [])

    render_form_header(form_id, form_name, form_desc, sections)
    st.write("")
    render_sections(form_id, content, sections)
    render_add_section_form(form_id, content, sections)
    render_form_preview(form_name, form_desc, sections)


def render_form_builder_page() -> None:
    init_page()
    st.divider()
    tab_list, tab_new = st.tabs([":material/assignment: My Forms", ":material/add: New Form"])

    with tab_list:
        render_forms_list_tab()

    with tab_new:
        render_new_form_tab()


render_form_builder_page()
