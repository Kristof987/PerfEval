def append_background_and_colour_stepper_style(css_rules, completed_until):
    for i in range(max(0, completed_until + 1)):
        css_rules.append(
            f"div[role='radiogroup'] > button:nth-child({i + 1}) {{"
            f"  background-color: #10B981 !important;"
            f"  color: #fff !important;"
            f"  border-color: #10B981 !important;"
            f"}}"
        )
def append_active_step_highlight(css_rules, current):
    css_rules.append(
        f"div[role='radiogroup'] > button:nth-child({current + 1}) {{"
        f"  box-shadow: inset 0 0 0 2px rgba(255,255,255,0.88), 0 0 0 3px rgba(16, 185, 129, 0.35), 0 0 0 5px rgba(16, 185, 129, 0.16) !important;"
        f"  border-color: #10B981 !important;"
        f"  transform: translateY(-1px);"
        f"}}"
    )