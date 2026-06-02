from dataclasses import dataclass

import pandas as pd
import streamlit as st

from ui.pages.campaigns.helpers.helpers import get


@dataclass(frozen=True)
class EvaluationSummary:
    remaining_by_evaluator: dict[str, int]
    completed_by_evaluator: dict[str, int]
    assigned_by_evaluator: dict[str, int]
    total_remaining: int
    total_completed: int
    total_assigned: int


def build_evaluation_summary(evaluations) -> EvaluationSummary:
    remaining_by_evaluator: dict[str, int] = {}
    completed_by_evaluator: dict[str, int] = {}
    assigned_by_evaluator: dict[str, int] = {}

    for row in evaluations:
        evaluator_name = str(get(row, "evaluator_name", "Unknown"))
        status = str(get(row, "status", "")).lower()
        assigned_by_evaluator[evaluator_name] = assigned_by_evaluator.get(evaluator_name, 0) + 1
        if status == "completed":
            completed_by_evaluator[evaluator_name] = completed_by_evaluator.get(evaluator_name, 0) + 1
        else:
            remaining_by_evaluator[evaluator_name] = remaining_by_evaluator.get(evaluator_name, 0) + 1

    return EvaluationSummary(
        remaining_by_evaluator=remaining_by_evaluator,
        completed_by_evaluator=completed_by_evaluator,
        assigned_by_evaluator=assigned_by_evaluator,
        total_remaining=sum(remaining_by_evaluator.values()),
        total_completed=sum(completed_by_evaluator.values()),
        total_assigned=sum(assigned_by_evaluator.values()),
    )


def render_evaluation_metrics(summary: EvaluationSummary) -> None:
    m1, m2, m3 = st.columns(3)
    m1.metric("Remaining questionnaires", summary.total_remaining)
    m2.metric("Completed questionnaires", summary.total_completed)
    m3.metric("Assigned questionnaires", summary.total_assigned)

    if summary.total_remaining == 0 and summary.total_assigned > 0:
        st.success("All questionnaires are completed.")
    elif summary.total_assigned == 0:
        st.info("No questionnaires assigned yet.")
    else:
        st.warning(f"{summary.total_remaining} questionnaires are still pending.")


def render_remaining_by_employee_table(summary: EvaluationSummary) -> None:
    if not summary.assigned_by_evaluator:
        return

    rows = []
    for evaluator_name, assigned_count in summary.assigned_by_evaluator.items():
        completed_count = summary.completed_by_evaluator.get(evaluator_name, 0)
        rows.append(
            {
                "Employee": evaluator_name,
                "Remaining": assigned_count - completed_count,
                "Completed": completed_count,
                "Assigned": assigned_count,
            }
        )

    rows = sorted(rows, key=lambda row: (-row["Remaining"], row["Employee"]))
    st.write("**Remaining questionnaires by employee**")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
