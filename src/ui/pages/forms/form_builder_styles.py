MATERIAL_SYMBOLS_CSS = (
    '<link rel="stylesheet" '
    'href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0"/>'
)

SECTION_HEADER_HTML = """<div style="background:#f8fafc;color:#0f172a;padding:{padding};
border-left:3px solid #cbd5e1;border-radius:6px;font-weight:600;{extra_style}
display:flex;align-items:center;gap:8px">
<span class="material-symbols-outlined" style="font-size:{icon_size};font-weight:400;line-height:1">folder</span>
{title}</div>"""

RATING_SCALE_HTML = """<div style='display:flex;gap:6px;margin:4px 0'>{badges}</div>"""

RATING_BADGE_HTML = (
    "<span style='background:#f0f2f6;border-radius:50%;width:30px;"
    "height:30px;display:flex;align-items:center;justify-content:center;"
    "font-size:0.85rem'>{value}</span>"
)

SLIDER_OPTIONS_HTML = """<div style='display:flex;gap:6px;margin:4px 0'>{chips}</div>"""

SLIDER_OPTION_CHIP_HTML = (
    "<span style='background:#e8f4f8;border-radius:8px;padding:4px 8px;"
    "font-size:0.8rem'>{label}</span>"
)

SCROLL_TO_ANCHOR_SCRIPT = """
<script>
  const jump = () => {{
    const el = window.parent.document.getElementById('{anchor_id}');
    if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }};
  setTimeout(jump, 80);
</script>
"""


def section_header_html(title: str, preview: bool = False) -> str:
    return SECTION_HEADER_HTML.format(
        title=title,
        padding="6px 12px" if preview else "8px 14px",
        icon_size="1.1rem" if preview else "1.2rem",
        extra_style="margin:12px 0 8px 0;" if preview else "font-size:1.05rem;margin-bottom:10px;",
    )


def rating_scale_html(low: int, high: int) -> str:
    badges = "".join(RATING_BADGE_HTML.format(value=value) for value in range(low, high + 1))
    return RATING_SCALE_HTML.format(badges=badges)


def slider_options_html(options: list[str]) -> str:
    chips = "".join(SLIDER_OPTION_CHIP_HTML.format(label=option) for option in options)
    return SLIDER_OPTIONS_HTML.format(chips=chips)


def scroll_to_anchor_script(anchor_id: str) -> str:
    return SCROLL_TO_ANCHOR_SCRIPT.format(anchor_id=anchor_id)
