#!/usr/bin/env python3
"""
result_generation/main.py

Entry point for AI-based result generation.
Accepts all questions and answers for a campaign as a JSON string
via a command-line argument or stdin.

Usage:
    python main.py '<json_string>'
    echo '<json_string>' | python main.py
"""

import sys
import os
import json

# Ensure the directory of this script is on the path so that
# sibling modules (base_metadata, llm_communication) can be imported.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_metadata import BaseMetadata


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

def _normalize_answer(answer) -> str:
    """Flatten a legacy dict-wrapper answer to a plain string."""
    if answer is None:
        return ""
    if isinstance(answer, dict):
        if "rating" in answer:
            return str(answer["rating"])
        if "choice" in answer:
            return str(answer["choice"])
        if "text" in answer:
            return str(answer["text"])
        return json.dumps(answer, ensure_ascii=False)
    return str(answer)


def process_campaign_data(data: dict) -> dict:
    """
    Process campaign evaluation data.

    Builds one :class:`BaseMetadata` instance for every question-answer pair
    found in the payload and returns a summary dict that is printed as JSON.

    Parameters
    ----------
    data : dict
        Expected structure::

            {
                "campaign_id":   int,
                "campaign_name": str,
                "evaluations": [
                    {
                        "evaluation_id":  int,
                        "evaluatee_name": str,
                        "evaluator_role": str,
                        "form_name":      str,
                        "finish_date":    str | None,
                        "qa_pairs": [
                            {
                                "question_id":   str,
                                "question":      str,
                                "question_type": str,
                                "section":       str,
                                "answer":        any
                            },
                            ...
                        ]
                    },
                    ...
                ]
            }

    Returns
    -------
    dict
        Summary with metadata objects serialised to JSON.
    """
    campaign_id   = data.get("campaign_id")
    campaign_name = data.get("campaign_name", "Unknown Campaign")
    evaluations   = data.get("evaluations", [])

    processed: list[dict] = []

    for evaluation in evaluations:
        evaluatee_name = evaluation.get("evaluatee_name", "Unknown")
        evaluator_role = evaluation.get("evaluator_role", "Unknown")
        form_name      = evaluation.get("form_name", "Unknown")
        finish_date    = evaluation.get("finish_date")
        qa_pairs       = evaluation.get("qa_pairs", [])

        for qa in qa_pairs:
            answer_raw = qa.get("answer")
            answer_str = _normalize_answer(answer_raw)

            metadata = BaseMetadata(
                question       = qa.get("question", ""),
                answer         = answer_str,
                question_type  = qa.get("question_type", "text"),
                competence     = qa.get("section", "General"),
                evaluator_role = evaluator_role,
            )

            processed.append({
                "evaluatee":   evaluatee_name,
                "form":        form_name,
                "finish_date": finish_date,
                "metadata":    json.loads(metadata.to_json()),
            })

    return {
        "campaign_id":         campaign_id,
        "campaign_name":       campaign_name,
        "total_evaluations":   len(evaluations),
        "total_qa_pairs":      len(processed),
        "processed_qa_pairs":  processed,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Accept JSON from the first positional argument …
    if len(sys.argv) > 1:
        json_input = sys.argv[1]
    else:
        # … or from stdin (piped usage)
        json_input = sys.stdin.read().strip()

    if not json_input:
        print(json.dumps({
            "error": "No input data provided. "
                     "Pass the campaign JSON as the first argument or via stdin."
        }))
        sys.exit(1)

    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"Invalid JSON input: {exc}"}))
        sys.exit(1)

    result = process_campaign_data(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
