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
import re

# Ensure sibling modules (base_metadata, llm_communication) and
# the top-level src/ directory (prompt.py) are importable.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)                                           # result_generation/
sys.path.insert(0, os.path.normpath(os.path.join(_here, "..", "..")))  # src/

from base_metadata import BaseMetadata
from llm_communication import LLMCommunication
from prompt import SYSTEM_PROMPT


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

    Builds one :class:`BaseMetadata` instance for every answer entry found in
    the payload and returns a summary dict that is printed as JSON.

    Parameters
    ----------
    data : dict
        Expected structure::

            {
                "campaign_id":   int,
                "campaign_name": str,
                "forms": {
                    "<form_name>": [
                        {
                            "question":      str,
                            "question_type": str,
                            "competence":    str,
                            "options":       list,   # optional
                            "answers": [
                                {
                                    "evaluatee_name": str,
                                    "evaluator_role": str,
                                    "answer":         any
                                },
                                ...
                            ]
                        },
                        ...
                    ],
                    ...
                }
            }

    Returns
    -------
    dict
        Summary with metadata objects serialised to JSON.
    """
    campaign_id   = data.get("campaign_id")
    campaign_name = data.get("campaign_name", "Unknown Campaign")
    forms         = data.get("forms", {})

    processed: list[dict] = []

    for form_name, questions in forms.items():
        for q in questions:
            question_text  = q.get("question", "")
            question_type  = q.get("question_type", "text")
            competence     = q.get("competence", "General")

            for answer_entry in q.get("answers", []):
                answer_str = _normalize_answer(answer_entry.get("answer"))

                metadata = BaseMetadata(
                    question       = question_text,
                    answer         = answer_str,
                    question_type  = question_type,
                    competence     = competence,
                    evaluator_role = answer_entry.get("evaluator_role", "Unknown"),
                )

                processed.append({
                    "form":           form_name,
                    "evaluatee":      answer_entry.get("evaluatee_name", "Unknown"),
                    "evaluator_role": answer_entry.get("evaluator_role", "Unknown"),
                    "metadata":       json.loads(metadata.to_json()),
                })

    return {
        "campaign_id":        campaign_id,
        "campaign_name":      campaign_name,
        "total_forms":        len(forms),
        "total_qa_pairs":     len(processed),
        "processed_qa_pairs": processed,
    }


# ---------------------------------------------------------------------------
# LLM result generation
# ---------------------------------------------------------------------------

def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers that some LLMs emit."""
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*([\s\S]*?)```$", text)
    if match:
        return match.group(1).strip()
    return text


def generate_llm_results(processed: dict) -> dict:
    """
    For every unique evaluatee in *processed*, build a prompt from
    SYSTEM_PROMPT + their Q&A metadata and call the LLM.

    Returns
    -------
    dict
        {
            "campaign_id":   int,
            "campaign_name": str,
            "results": {
                "<evaluatee_name>": { ...LLM JSON output... }
            }
        }
    """
    llm = LLMCommunication()

    # Group processed_qa_pairs by evaluatee
    by_evaluatee: dict = {}
    for item in processed.get("processed_qa_pairs", []):
        name = item.get("evaluatee", "Unknown")
        by_evaluatee.setdefault(name, []).append(item["metadata"])

    results: dict = {}
    for evaluatee_name, metadata_list in by_evaluatee.items():
        full_prompt = (
            SYSTEM_PROMPT
            + "\n\nInput data (JSON):\n"
            + json.dumps(metadata_list, ensure_ascii=False, indent=2)
        )
        raw_response = llm.request(full_prompt)
        cleaned = _strip_markdown_fences(raw_response)
        try:
            results[evaluatee_name] = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            results[evaluatee_name] = {"raw_response": raw_response}

    return {
        "campaign_id":   processed.get("campaign_id"),
        "campaign_name": processed.get("campaign_name"),
        "results":       results,
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

    processed = process_campaign_data(data)
    llm_output = generate_llm_results(processed)
    print(json.dumps(llm_output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
