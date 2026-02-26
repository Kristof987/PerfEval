import streamlit as st
import json
import uuid
from database.connection import get_connection

# ─── Page header ──────────────────────────────────────────────────────────────
st.title("📋 Form Builder")
st.write("Create and manage performance evaluation forms with sections and questions.")

# ─── Session state ────────────────────────────────────────────────────────────
if "fb_current_form_id" not in st.session_state:
    st.session_state.fb_current_form_id = None

# ─── Constants ────────────────────────────────────────────────────────────────
QUESTION_TYPES = {
    "text":            ("📝", "Text Response (open-ended)"),
    "multiple_choice": ("☑️", "Multiple Choice"),
    "rating":          ("⭐", "Rating Scale"),
}

# ─── Data helpers ─────────────────────────────────────────────────────────────

def _uid() -> str:
    return str(uuid.uuid4())[:8]


def new_section(title: str) -> dict:
    return {"id": _uid(), "title": title, "questions": []}


def new_question(text: str, qtype: str, required: bool = True,
                 options: list = None, rating_min: int = 1, rating_max: int = 5) -> dict:
    q: dict = {"id": _uid(), "text": text, "type": qtype, "required": required}
    if qtype == "multiple_choice":
        q["options"] = options or []
    elif qtype == "rating":
        q["rating_min"] = rating_min
        q["rating_max"] = rating_max
    return q


def migrate_content(raw) -> dict:
    """Convert old flat-list questions format to the new {sections:[...]} format."""
    if isinstance(raw, list):
        return {
            "sections": [
                {"id": "legacy", "title": "General", "questions": raw}
            ]
        }
    if isinstance(raw, dict) and "sections" in raw:
        return raw
    return {"sections": []}


# ─── Database helpers ─────────────────────────────────────────────────────────

def db_get_all_forms() -> list:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, description FROM form ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows
    except Exception as e:
        st.error(f"Error fetching forms: {e}")
        return []


def db_create_form(name: str, description: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO form (name, description, questions) VALUES (%s, %s, %s) RETURNING id",
            (name, description, json.dumps({"sections": []}))
        )
        form_id = cur.fetchone()[0]
        conn.commit(); cur.close(); conn.close()
        return form_id
    except Exception as e:
        st.error(f"Error creating form: {e}")
        return None


def db_get_form(form_id: int):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, questions FROM form WHERE id = %s", (form_id,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return row
    except Exception as e:
        st.error(f"Error loading form: {e}")
        return None


def db_save_form(form_id: int, content: dict) -> bool:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE form SET questions = %s WHERE id = %s",
                    (json.dumps(content), form_id))
        conn.commit(); cur.close(); conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving form: {e}")
        return False


def db_delete_form(form_id: int) -> bool:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM form WHERE id = %s", (form_id,))
        conn.commit(); cur.close(); conn.close()
        return True
    except Exception as e:
        st.error(f"Error deleting form: {e}")
        return False


# ─── UI ───────────────────────────────────────────────────────────────────────

st.divider()
tab_list, tab_new = st.tabs(["📋 My Forms", "➕ New Form"])

# ── New Form tab ───────────────────────────────────────────────────────────────
with tab_new:
    st.subheader("Create New Form")
    with st.form("fb_create_form"):
        nf_title = st.text_input("Form title *", placeholder="e.g., Q1 2024 Performance Review")
        nf_desc  = st.text_area("Description", placeholder="Describe the purpose of this form…")
        if st.form_submit_button("Create Form", type="primary"):
            if not nf_title.strip():
                st.error("❌ Please enter a form title.")
            else:
                fid = db_create_form(nf_title.strip(), nf_desc.strip())
                if fid:
                    st.success(f"✅ Form **{nf_title}** created!")
                    st.session_state.fb_current_form_id = fid
                    st.rerun()

# ── My Forms tab ──────────────────────────────────────────────────────────────
with tab_list:
    all_forms = db_get_all_forms()

    if not all_forms:
        st.info("No forms yet. Switch to **➕ New Form** to create one.")
        st.stop()

    # ── Form selector ──────────────────────────────────────────────────────
    form_options = {f"{f[1]}  (ID: {f[0]})": f[0] for f in all_forms}
    default_idx = 0
    if st.session_state.fb_current_form_id in form_options.values():
        default_idx = list(form_options.values()).index(st.session_state.fb_current_form_id)

    selected_key = st.selectbox("Select form to edit:", list(form_options.keys()), index=default_idx)
    selected_id  = form_options[selected_key]
    st.session_state.fb_current_form_id = selected_id

    form_row = db_get_form(selected_id)
    if not form_row:
        st.error("Could not load the selected form.")
        st.stop()

    form_id, form_name, form_desc, questions_raw = form_row
    content  = migrate_content(questions_raw)
    sections = content.get("sections", [])

    # ── Form header card ───────────────────────────────────────────────────
    with st.container(border=True):
        hcol1, hcol2 = st.columns([5, 1])
        with hcol1:
            st.markdown(f"## {form_name}")
            if form_desc:
                st.caption(form_desc)
            total_q = sum(len(s.get("questions", [])) for s in sections)
            st.caption(f"**{total_q}** question(s) across **{len(sections)}** section(s)")
        with hcol2:
            if st.button("🗑️ Delete form", key=f"del_form_{form_id}"):
                if db_delete_form(form_id):
                    st.session_state.fb_current_form_id = None
                    st.success("Form deleted.")
                    st.rerun()

    st.write("")

    # ── Sections ──────────────────────────────────────────────────────────
    for sec_idx, section in enumerate(sections):
        sec_id    = section.get("id", sec_idx)
        sec_title = section.get("title", f"Section {sec_idx + 1}")
        questions = section.get("questions", [])

        with st.container(border=True):
            # Section title row
            st.markdown(
                f"""<div style="background:#4285F4;color:white;padding:8px 14px;
                border-radius:6px;font-weight:600;font-size:1.05rem;margin-bottom:10px">
                📂 {sec_title}</div>""",
                unsafe_allow_html=True
            )

            sec_ctrl1, sec_ctrl2 = st.columns([6, 1])
            with sec_ctrl2:
                if st.button("🗑️ Section", key=f"del_sec_{form_id}_{sec_idx}",
                             help="Delete this section and all its questions"):
                    sections.pop(sec_idx)
                    content["sections"] = sections
                    db_save_form(form_id, content)
                    st.rerun()

            # Rename section
            with st.expander("✏️ Rename section", expanded=False):
                with st.form(f"fb_rename_sec_{form_id}_{sec_idx}"):
                    new_sec_name = st.text_input("New section name", value=sec_title,
                                                 label_visibility="collapsed")
                    if st.form_submit_button("Rename"):
                        if new_sec_name.strip():
                            sections[sec_idx]["title"] = new_sec_name.strip()
                            content["sections"] = sections
                            db_save_form(form_id, content)
                            st.rerun()

            st.divider()

            # Questions list
            if not questions:
                st.caption("_No questions yet in this section._")
            else:
                for q_idx, q in enumerate(questions):
                    type_icon  = QUESTION_TYPES.get(q.get("type", "text"), ("❓", "Unknown"))[0]
                    type_label = QUESTION_TYPES.get(q.get("type", "text"), ("❓", "Unknown"))[1]
                    req_star   = " \\*" if q.get("required") else ""

                    qcol1, qcol2 = st.columns([10, 1])
                    with qcol1:
                        st.markdown(f"{type_icon} **{q['text']}{req_star}**")
                        st.caption(f"_{type_label}_")

                        if q.get("type") == "multiple_choice" and q.get("options"):
                            for opt in q["options"]:
                                st.write(f"&nbsp;&nbsp;○ {opt}")
                        elif q.get("type") == "rating":
                            lo = q.get("rating_min", 1)
                            hi = q.get("rating_max", 5)
                            scale_str = "  ".join(str(i) for i in range(lo, hi + 1))
                            st.markdown(
                                f"<div style='display:flex;gap:6px;margin:4px 0'>"
                                + "".join(
                                    f"<span style='background:#f0f2f6;border-radius:50%;width:30px;"
                                    f"height:30px;display:flex;align-items:center;justify-content:center;"
                                    f"font-size:0.85rem'>{i}</span>"
                                    for i in range(lo, hi + 1)
                                )
                                + "</div>",
                                unsafe_allow_html=True
                            )
                    with qcol2:
                        if st.button("🗑️", key=f"del_q_{form_id}_{sec_idx}_{q_idx}",
                                     help="Delete question"):
                            sections[sec_idx]["questions"].pop(q_idx)
                            content["sections"] = sections
                            db_save_form(form_id, content)
                            st.rerun()

                    st.write("")

            # ── Add Question form (inside expander for this section) ───────
            with st.expander(f"➕ Add question to \"{sec_title}\"", expanded=False):
                with st.form(f"fb_add_q_{form_id}_{sec_idx}"):
                    aq_text = st.text_input(
                        "Question text *",
                        placeholder="Type your question here…"
                    )
                    aq_type = st.selectbox(
                        "Question type",
                        options=list(QUESTION_TYPES.keys()),
                        format_func=lambda t: f"{QUESTION_TYPES[t][0]}  {QUESTION_TYPES[t][1]}"
                    )
                    aq_required = st.checkbox("Required", value=True)

                    st.write("---")
                    st.caption("**Multiple Choice** — fill options below (one per line):")
                    aq_options_raw = st.text_area(
                        "Options (one per line)",
                        placeholder="Option A\nOption B\nOption C",
                        label_visibility="collapsed"
                    )

                    st.caption("**Rating Scale** — set lower and upper bound:")
                    rc1, rc2 = st.columns(2)
                    with rc1:
                        aq_rating_min = st.number_input("Min", min_value=0, max_value=9, value=1)
                    with rc2:
                        aq_rating_max = st.number_input("Max", min_value=1, max_value=10, value=5)

                    if st.form_submit_button("Add Question", type="primary"):
                        if not aq_text.strip():
                            st.error("❌ Please enter a question text.")
                        elif aq_type == "multiple_choice" and not aq_options_raw.strip():
                            st.error("❌ Please enter at least one option.")
                        elif aq_type == "rating" and aq_rating_min >= aq_rating_max:
                            st.error("❌ Min value must be less than Max value.")
                        else:
                            opts = (
                                [o.strip() for o in aq_options_raw.splitlines() if o.strip()]
                                if aq_type == "multiple_choice" else None
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
                            if db_save_form(form_id, content):
                                st.success("✅ Question added!")
                                st.rerun()

        st.write("")  # spacing between section cards

    # ── Add Section form ──────────────────────────────────────────────────
    st.divider()
    with st.form(f"fb_add_sec_{form_id}"):
        ns_col1, ns_col2 = st.columns([4, 1])
        with ns_col1:
            new_sec_title = st.text_input(
                "New section name",
                placeholder="e.g., Leadership Skills",
                label_visibility="collapsed"
            )
        with ns_col2:
            add_sec_btn = st.form_submit_button("➕ Add Section", type="secondary",
                                                use_container_width=True)
        if add_sec_btn:
            if not new_sec_title.strip():
                st.error("❌ Please enter a section name.")
            else:
                sections.append(new_section(new_sec_title.strip()))
                content["sections"] = sections
                if db_save_form(form_id, content):
                    st.success(f"✅ Section **{new_sec_title}** added!")
                    st.rerun()

    # ── Preview ───────────────────────────────────────────────────────────
    if sections and any(s.get("questions") for s in sections):
        st.divider()
        with st.expander("👁️ Form Preview", expanded=False):
            st.markdown(f"## {form_name}")
            if form_desc:
                st.write(form_desc)
            st.divider()

            q_global = 1
            for section in sections:
                st.markdown(
                    f"""<div style="background:#4285F4;color:white;padding:6px 12px;
                    border-radius:6px;font-weight:600;margin:12px 0 8px 0">
                    {section['title']}</div>""",
                    unsafe_allow_html=True
                )
                for q in section.get("questions", []):
                    req_mark = " *" if q.get("required") else ""
                    st.markdown(f"**{q_global}. {q['text']}{req_mark}**")

                    if q.get("type") == "text":
                        st.text_area("Your answer", key=f"prev_t_{q['id']}", disabled=True, height=90)
                    elif q.get("type") == "multiple_choice":
                        for opt in q.get("options", []):
                            st.write(f"○ {opt}")
                    elif q.get("type") == "rating":
                        lo, hi = q.get("rating_min", 1), q.get("rating_max", 5)
                        st.slider(
                            "Rating", min_value=lo, max_value=hi,
                            value=lo, key=f"prev_r_{q['id']}", disabled=True
                        )
                    st.write("")
                    q_global += 1
