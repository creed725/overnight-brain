"""The kinds of things you can hand off before bed, and how each is asked."""

KINDS = {
    "ask": {
        "label": "Answer a question",
        "hint": "Something you've been meaning to look into",
        "template": (
            "Answer this question clearly and practically in under 250 words. "
            "If you're not sure about something, say so.\n\nQuestion: {text}"
        ),
    },
    "summarize": {
        "label": "Summarize this",
        "hint": "Paste an article, notes, or a long email",
        "template": (
            "Summarize the following in 5 bullet points or fewer, then add one "
            "sentence on what matters most.\n\n{text}"
        ),
    },
    "plan": {
        "label": "Break it into steps",
        "hint": "A goal that feels too big to start",
        "template": (
            "Turn this goal into a short, realistic plan of at most 7 steps. "
            "End by naming the very first small step.\n\nGoal: {text}"
        ),
    },
    "draft": {
        "label": "Draft a message",
        "hint": "An email or text you keep putting off",
        "template": (
            "Write a friendly, concise draft for the request below. "
            "Return only the draft.\n\nRequest: {text}"
        ),
    },
}

DIGEST_PROMPT = (
    "Write a short, warm good-morning note. Below are tasks that were finished "
    "overnight and their results. In 2-3 sentences, say what got done and which "
    "result deserves attention first. Don't repeat the results themselves.\n\n{items}"
)
