import json
import os
import subprocess
import sys

import streamlit as st

from ui.pages.results.charts import render_summary_dashboard
from ui.pages.results.consts import AI_CARD_BASE_STYLE, AI_LABEL_BASE_STYLE
from ui.pages.results.excel_export import build_ai_excel
from ui.pages.results.results_styles import (
    area_cards_html,
    item_rows_html,
    strength_cards_html,
)


def render_answer(answer, question: dict):
    q_type = question.get("type", "text")
    if answer is None or answer == "":
        st.caption("_(no answer)_")
        return

    if isinstance(answer, dict):
        if "rating" in answer:
            hi = question.get("rating_max", 5)
            st.write(f"⭐ {answer['rating']}/{hi}")
        if "choice" in answer:
            st.write(f"☑️ {answer['choice']}")
        if "text" in answer:
            st.write(f"📝 {answer['text']}")
        return

    if q_type == "rating":
        hi = question.get("rating_max", 5)
        st.write(f"⭐ {answer}/{hi}")
    elif q_type == "multiple_choice":
        st.write(f"☑️ {answer}")
    elif q_type == "slider_labels":
        st.write(f"🎚️ {answer}")
    else:
        st.write(f"📝 {answer}")


def go_back_to_campaign_results():
    st.session_state.cr_view = "campaign"
    st.session_state.cr_selected_employee_id = None
    st.session_state.cr_selected_employee_name = None
    st.rerun()


def get_distinct_forms(evaluations):
    seen_form_ids = set()
    form_ids = []
    form_name_by_id = {}
    for evaluation in evaluations:
        form_id = evaluation["form_id"]
        if form_id not in seen_form_ids:
            seen_form_ids.add(form_id)
            form_ids.append(form_id)
            form_name_by_id[form_id] = evaluation["form_name"]
    return form_ids, form_name_by_id


def render_form_filter(form_ids, form_name_by_id, key_prefix):
    if len(form_ids) <= 1:
        return form_ids

    return st.multiselect(
        "Filter by form",
        options=form_ids,
        default=form_ids,
        format_func=lambda fid: form_name_by_id.get(fid, str(fid)),
        placeholder="Select forms to display…",
        key=f"{key_prefix}_form_filter",
    )


def group_evaluations_by_form_and_role(evaluations):
    evals_by_form = {}
    for evaluation in evaluations:
        evals_by_form.setdefault(evaluation["form_name"], {}).setdefault(
            evaluation["evaluator_role"], []
        ).append(evaluation)
    return evals_by_form


def render_question_answers(role_evals, question):
    q_id = str(question.get("id", ""))
    q_text = question.get("text", "Question")
    with st.container(border=True):
        st.markdown(f"**{q_text}**")
        any_answer = False
        for evaluation in role_evals:
            answer = evaluation["answers"].get(q_id)
            if answer is not None and answer != "":
                render_answer(answer, question)
                any_answer = True
        if not any_answer:
            st.caption("_(no answers)_")


def render_form_answers(form_name, roles_dict):
    st.subheader(f"📋 {form_name}")
    first_eval = next(iter(next(iter(roles_dict.values()))))
    sections = first_eval["sections"]
    if not sections:
        st.caption("_(no questions in this form)_")
    else:
        for role_name, role_evals in roles_dict.items():
            st.markdown(f"#### 👤 {role_name}")
            for section in sections:
                sec_title = section.get("title", "")
                questions = section.get("questions", [])
                if sec_title:
                    st.markdown(f"**{sec_title}**")
                for question in questions:
                    if isinstance(question, dict):
                        render_question_answers(role_evals, question)
    st.divider()


def render_grouped_answers(evaluations: list, key_prefix: str = "answers"):
    if not evaluations:
        st.info("No completed evaluations found for this employee in this campaign.")
        return

    form_ids, form_name_by_id = get_distinct_forms(evaluations)
    selected_form_ids = render_form_filter(form_ids, form_name_by_id, key_prefix)
    filtered_evals = [evaluation for evaluation in evaluations if evaluation["form_id"] in selected_form_ids]
    if not filtered_evals:
        st.info("No evaluations match the selected forms.")
        return

    evals_by_form = group_evaluations_by_form_and_role(filtered_evals)
    for form_name, roles_dict in evals_by_form.items():
        render_form_answers(form_name, roles_dict)


def split_self_and_role_evaluations(evaluations, employee_name):
    selected_emp_name = (employee_name or "").strip().lower()
    self_evaluations = [
        evaluation for evaluation in evaluations
        if (evaluation.get("evaluator_name") or "").strip().lower() == selected_emp_name
    ]
    non_self_evaluations = [
        evaluation for evaluation in evaluations
        if (evaluation.get("evaluator_name") or "").strip().lower() != selected_emp_name
    ]
    return self_evaluations, non_self_evaluations


def get_role_names(evaluations):
    role_names = []
    for evaluation in evaluations:
        role_name = evaluation.get("evaluator_role") or "Unknown"
        if role_name not in role_names:
            role_names.append(role_name)
    return role_names


def render_role_feedback_tabs(subpages, role_names, non_self_evaluations):
    for idx, role_name in enumerate(role_names):
        with subpages[idx + 2]:
            role_evals = [evaluation for evaluation in non_self_evaluations if evaluation.get("evaluator_role") == role_name]
            render_grouped_answers(role_evals, key_prefix=f"results_role_{idx}")

    if not role_names:
        with subpages[2]:
            st.info("No role-based feedback available yet for this employee.")


def get_ai_script_path():
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "services", "result_generation", "main.py",
        )
    )


def run_ai_pipeline(employee_payload):
    with st.spinner("Running AI analysis…"):
        return subprocess.run(
            [sys.executable, get_ai_script_path(), json.dumps(employee_payload)],
            capture_output=True,
            text=True,
            timeout=120,
        )


def render_top_highlights(analysis):
    top_strengths = analysis.get("top_strengths", [])
    top_development_areas = analysis.get("top_development_areas", [])
    if not top_strengths and not top_development_areas:
        return

    col_strengths, col_development = st.columns(2)
    with col_strengths:
        st.markdown(
            f'<div style="{AI_CARD_BASE_STYLE}min-height:0;">'
            f'<div style="{AI_LABEL_BASE_STYLE}">Top Strengths</div>'
            f'{item_rows_html(top_strengths, "#22c55e")}'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_development:
        st.markdown(
            f'<div style="{AI_CARD_BASE_STYLE}min-height:0;">'
            f'<div style="{AI_LABEL_BASE_STYLE}">Top Development Areas</div>'
            f'{item_rows_html(top_development_areas, "#f59e0b")}'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_role_based_analysis(analysis):
    role_based = analysis.get("role_based_analysis", {})
    if not isinstance(role_based, dict) or not role_based:
        return False

    st.markdown(
        f'<div style="{AI_LABEL_BASE_STYLE}margin-top:1rem;">Role-based Analysis</div>',
        unsafe_allow_html=True,
    )
    role_tabs = st.tabs(list(role_based.keys()))
    for role_tab, (_, role_data) in zip(role_tabs, role_based.items()):
        with role_tab:
            strengths = role_data.get("strengths", []) if isinstance(role_data, dict) else []
            areas = role_data.get("areas_for_improvement", []) if isinstance(role_data, dict) else []
            col_strengths, col_areas = st.columns(2)
            with col_strengths:
                if strengths:
                    st.markdown(
                        f'<div style="{AI_LABEL_BASE_STYLE}">Strengths</div>'
                        f'{strength_cards_html(strengths)}',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("No strengths identified for this role.")
            with col_areas:
                if areas:
                    st.markdown(
                        f'<div style="{AI_LABEL_BASE_STYLE}">Areas for Improvement</div>'
                        f'{area_cards_html(areas)}',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("No areas for improvement identified for this role.")
    return True


def render_basic_strengths_and_areas(analysis):
    strengths = analysis.get("strengths", [])
    areas = analysis.get("areas_for_improvement", [])
    if not strengths and not areas:
        return

    col_strengths, col_areas = st.columns(2)
    with col_strengths:
        if strengths:
            st.markdown(
                f'<div style="{AI_LABEL_BASE_STYLE}">Strengths</div>'
                f'{strength_cards_html(strengths)}',
                unsafe_allow_html=True,
            )
    with col_areas:
        if areas:
            st.markdown(
                f'<div style="{AI_LABEL_BASE_STYLE}">Areas for Improvement</div>'
                f'{area_cards_html(areas)}',
                unsafe_allow_html=True,
            )


def render_ai_summary(analysis):
    summary = analysis.get("summary", "")
    if summary:
        st.markdown(
            f'<div style="{AI_CARD_BASE_STYLE}margin-top:0.5rem;min-height:0;">'
            f'<div style="{AI_LABEL_BASE_STYLE}">Summary</div>'
            f'<div style="font-size:0.87rem;color:#1a2035;line-height:1.6;">{summary}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_confidence(analysis):
    confidence_level = analysis.get("confidence_level", "")
    confidence_reason = analysis.get("confidence_reason", "")
    if not confidence_level:
        return

    confidence_dot = {"high": "#22c55e", "medium": "#f59e0b", "low": "#ef4444"}.get(confidence_level, "#94a3b8")
    st.markdown(
        f'<div style="display:inline-flex;align-items:center;gap:7px;margin-top:6px;">'
        f'<span style="width:8px;height:8px;border-radius:50%;background:{confidence_dot};flex-shrink:0;"></span>'
        f'<span style="font-size:0.8rem;color:#475569;">'
        f'<b style="color:#0f172a;">Confidence: {confidence_level.capitalize()}</b>'
        f' — {confidence_reason}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def get_excel_template_path():
    return os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..", "..",
        "datafiles", "eval_output_sample.xlsx",
    ))


def render_ai_excel_export(campaign_results_service, evaluations, analysis, emp_name, campaign_id):
    employee_id = st.session_state.cr_selected_employee_id
    metadata = campaign_results_service.get_employee_result_export_metadata(
        employee_id,
        campaign_id,
        emp_name,
    )
    xlsx_bytes = build_ai_excel(
        emp_name=metadata["name"],
        emp_email=metadata["email"],
        emp_role=metadata["role"],
        camp_name=st.session_state.cr_selected_campaign_name,
        submitted_count=metadata["submitted_count"],
        evaluations=evaluations,
        analysis=analysis,
        template_path=get_excel_template_path(),
    )
    st.download_button(
        label="⬇️ Export to Excel",
        data=xlsx_bytes,
        file_name=f"ai_analysis_{emp_name.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_export_ai_excel",
    )


def render_analysis_details(campaign_results_service, evaluations, analysis, emp_name, campaign_id):
    with st.expander("🔍 Raw LLM output (JSON)", expanded=False):
        st.json(analysis)
    render_top_highlights(analysis)
    if not render_role_based_analysis(analysis):
        render_basic_strengths_and_areas(analysis)
    render_ai_summary(analysis)
    render_confidence(analysis)
    render_ai_excel_export(campaign_results_service, evaluations, analysis, emp_name, campaign_id)


def render_ai_result(campaign_results_service, evaluations, proc, emp_name, campaign_id):
    if proc.returncode != 0:
        st.error("❌ Pipeline returned an error.")
        with st.expander("Error details"):
            st.code(proc.stderr or proc.stdout)
        return

    st.success("✅ Analysis finished.")
    try:
        output = json.loads(proc.stdout)
        analysis = output.get("results", {}).get(emp_name, {})
        if not analysis:
            st.json(output)
        elif "raw_response" in analysis:
            st.code(analysis["raw_response"])
        else:
            render_analysis_details(campaign_results_service, evaluations, analysis, emp_name, campaign_id)
    except (json.JSONDecodeError, ValueError):
        st.code(proc.stdout)


def render_ai_analysis(db, campaign_results_service, evaluations, campaign_id):
    st.divider()
    st.subheader("🤖 AI Analysis")
    if not st.button(
        "Generate AI Results",
        key="btn_generate_ai_results_emp",
        type="primary",
        help="Run the AI pipeline for this employee's completed evaluations.",
    ):
        return

    emp_name = st.session_state.cr_selected_employee_name
    employee_payload = campaign_results_service.build_employee_qa_json(
        st.session_state.cr_selected_campaign_id,
        st.session_state.cr_selected_campaign_name,
        emp_name,
        evaluations,
    )
    proc = run_ai_pipeline(employee_payload)
    render_ai_result(campaign_results_service, evaluations, proc, emp_name, campaign_id)


def render_summary_tab(db, campaign_results_service, evaluations, campaign_id):
    if not evaluations:
        st.info("No completed evaluations found for this employee in this campaign.")
        return

    render_summary_dashboard(evaluations, key_prefix="emp")
    render_ai_analysis(db, campaign_results_service, evaluations, campaign_id)


def render_results_tab(db, campaign_results_service, evaluations, campaign_id):
    employee_name = st.session_state.cr_selected_employee_name
    self_evaluations, non_self_evaluations = split_self_and_role_evaluations(evaluations, employee_name)
    role_names = get_role_names(non_self_evaluations)
    subpage_labels = ["Summary", "Self Evaluation"] + [f"{role_name} Role Feedback" for role_name in role_names]
    if not role_names:
        subpage_labels.append("Role Feedback")

    subpages = st.tabs(subpage_labels)
    with subpages[1]:
        render_grouped_answers(self_evaluations, key_prefix="results_self")
    render_role_feedback_tabs(subpages, role_names, non_self_evaluations)
    with subpages[0]:
        render_summary_tab(db, campaign_results_service, evaluations, campaign_id)


def render_employee_view(db, campaign_results_service):
    st.title(f"Employee Evaluation Results - {st.session_state.cr_selected_employee_name}")
    st.caption(f"Campaign: {st.session_state.cr_selected_campaign_name}")
    st.divider()

    employee_id = st.session_state.cr_selected_employee_id
    campaign_id = st.session_state.cr_selected_campaign_id
    evaluations = campaign_results_service.get_evaluations_for_employee(employee_id, campaign_id)
    tab_answers, tab_results = st.tabs(["📝 Answers", "📊 Results"])
    with tab_answers:
        render_grouped_answers(evaluations, key_prefix="answers_all")
    with tab_results:
        render_results_tab(db, campaign_results_service, evaluations, campaign_id)

    st.divider()
    if st.button("← Back to Campaign Results", key="btn_back_campaign_results_bottom"):
        go_back_to_campaign_results()
