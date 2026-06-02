import streamlit as st


def render_question_input(evaluation_id, question, idx, answers):
    q_id = question.get("id", idx)
    q_text = question.get("text", "")
    q_type = question.get("type", "Text Response")

    st.write(f"**{idx}. {q_text}**")

    if q_type == "text":
        answers[q_id] = st.text_area(
            "Your answer",
            key=f"answer_{evaluation_id}_{q_id}",
        )
    elif q_type == "multiple_choice":
        options = question.get("options", [])
        answers[q_id] = st.radio(
            "Select one",
            options,
            key=f"answer_{evaluation_id}_{q_id}",
        )
    elif q_type == "rating":
        lo = question.get("rating_min", 1)
        hi = question.get("rating_max", 5)
        answers[q_id] = st.slider(
            "Rating",
            min_value=lo,
            max_value=hi,
            value=lo,
            key=f"answer_{evaluation_id}_{q_id}",
        )
    elif q_type == "slider_labels":
        options = question.get("slider_options", [])
        if options:
            answers[q_id] = st.radio(
                "Select value",
                options=[f"{i + 1}. {str(opt)}" for i, opt in enumerate(options)],
                key=f"answer_{evaluation_id}_{q_id}",
                horizontal=True,
            )
            if answers[q_id]:
                parts = answers[q_id].split(". ", 1)
                answers[q_id] = parts[1] if len(parts) > 1 else answers[q_id]

    st.write("")
