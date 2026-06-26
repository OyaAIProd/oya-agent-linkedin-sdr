import os, json, httpx

SYSTEM_PROMPT = (
    "You are an expert professional communication assistant specializing in LinkedIn. "
    "Your job is to analyze a LinkedIn conversation and produce a single JSON object with these fields:\n"
    "- suggested_reply: A professional, concise, context-aware reply (2-4 sentences). "
    "Never start with 'I hope this message finds you well.'\n"
    "- intent_tag: One of: sales_pitch, job_opportunity, collaboration, follow_up, networking, recruiting, spam, unclear\n"
    "- confidence_level: A float between 0.0 and 1.0 reflecting confidence in intent classification and reply quality\n"
    "- needs_human_review: true if the conversation is sensitive, ambiguous, contains a legal/financial offer, "
    "involves distress, or confidence_level < 0.6; otherwise false\n"
    "- reasoning: One sentence explaining your intent classification\n\n"
    "Respond ONLY with the raw JSON object. No markdown, no code fences, no extra text."
)


def build_conversation_text(message_history):
    lines = []
    for msg in message_history:
        role = msg.get("role", "unknown").upper()
        text = msg.get("text", "").strip()
        lines.append(f"{role}: {text}")
    return "\n".join(lines)


def get_last_message_snippet(message_history, max_len=120):
    for msg in reversed(message_history):
        text = msg.get("text", "").strip()
        if text:
            return (text[:max_len] + "...") if len(text) > max_len else text
    return ""


def strip_fences(raw):
    raw = raw.strip()
    if raw.startswith("