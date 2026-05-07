from datetime import date, datetime
import streamlit as st

def get(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def datetime_to_string(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)

def to_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text).date()
        except Exception:
            return None
    return None

def count_days_left(end_value) -> int | None:
    end_date = to_date(end_value)
    if not end_date:
        return None
    return (end_date - date.today()).days


def date_to_datetime(d):
    return datetime.combine(d, datetime.min.time()) if d else None
