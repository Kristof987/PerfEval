from __future__ import annotations

import json
from typing import Any, Dict


def normalize_questions(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {"sections": []}

    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {"sections": []}
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return {"sections": []}

    if isinstance(raw, list):
        return {"sections": [{"id": "legacy", "title": "General", "questions": raw}]}

    if isinstance(raw, dict) and "sections" in raw:
        return raw

    return {"sections": []}

