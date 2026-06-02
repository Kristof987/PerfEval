DASHBOARD_COMPACT_CSS = """
<style>
    html, body, [class*="css"] {
        font-size: 14px;
    }

    h1, h2, h3 {
        font-size: 0.92em;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.15rem;
    }

    .stButton > button {
        font-size: 0.82rem;
        padding-top: 0.28rem;
        padding-bottom: 0.28rem;
    }
</style>
"""

SECTION_TITLE_HTML = (
    "<p style='font-size:12px;font-weight:500;color:#888;text-transform:uppercase;"
    "letter-spacing:.4px;margin-bottom:4px'>{title}</p>"
)

COMPACT_CAMPAIGN_META_HTML = "<p style='margin:0;color:#6b7280;font-size:12px'>{text}</p>"

COMPACT_CAMPAIGN_TITLE_HTML = "<span style='font-size:0.9rem;font-weight:600'>{name}</span>"


def status_badge_html(label: str, fg: str, bg: str, compact: bool = False) -> str:
    padding = "2px 8px" if compact else "4px 12px"
    font_size = "10px" if compact else "12px"
    font_weight = "500" if compact else "600"
    return (
        f"<span style='background:{bg};color:{fg};padding:{padding};"
        f"border-radius:20px;font-size:{font_size};font-weight:{font_weight}'>{label}</span>"
    )


def section_title_html(title: str) -> str:
    return SECTION_TITLE_HTML.format(title=title)


def compact_campaign_title_html(name: str) -> str:
    return COMPACT_CAMPAIGN_TITLE_HTML.format(name=name)


def compact_campaign_meta_html(text: str) -> str:
    return COMPACT_CAMPAIGN_META_HTML.format(text=text)
