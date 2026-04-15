import pandas as pd
from dataclasses import dataclass
from typing import List

from consts.consts import TEMPLATE_COLUMNS


ROLE_ALIASES = {
    "manager": "management",
    "teamlead": "team leader",
    "team lead": "team leader",
    "hr": "hr employee",
}


@dataclass(frozen=True)
class ImportedEmployeeRow:
    name: str
    email: str
    org_role: str | None
    system_role: str


def _normalize_role_name(role_name: str) -> str:
    normalized = " ".join(role_name.strip().lower().replace("_", " ").replace("-", " ").split())
    return ROLE_ALIASES.get(normalized, normalized)


def _normalize_email(email: str) -> str:
    normalized = email.strip()
    if " (mailto:" in normalized:
        normalized = normalized.split(" (mailto:", 1)[0].strip()
    return normalized


def parse_employees_from_template(uploaded_file) -> List[ImportedEmployeeRow]:
    df = pd.read_excel(uploaded_file)
    missing_columns = [col for col in TEMPLATE_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns: {', '.join(missing_columns)}")

    rows: List[ImportedEmployeeRow] = []
    for _, row in df.iterrows():
        name = str(row["Employee Name"]).strip()
        email = _normalize_email(str(row["Employee Email Address"]))
        org_role_raw = str(row["Employee Organisation Role"]).strip()
        system_role_raw = str(row["Employee System Role"]).strip()

        rows.append(
            ImportedEmployeeRow(
                name=name,
                email=email,
                org_role=org_role_raw if org_role_raw and org_role_raw.lower() != "nan" else None,
                system_role=_normalize_role_name(system_role_raw),
            )
        )

    return rows
