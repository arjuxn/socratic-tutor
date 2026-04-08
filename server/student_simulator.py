import os
import re
from typing import List, Optional
from openai import OpenAI


def _get_client():
    return OpenAI(
        base_url=os.getenv("API_BASE_URL", "https://router.huggingface.co/v1"),
        api_key=os.getenv("HF_TOKEN") or os.getenv("API_KEY", ""),
    )

MODEL = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")


def get_student_response(teacher_utterance, misconception, correct_answer, history, temperature=0.4):
    client = _get_client()
    history_text = ""
    if history:
        for turn in history[-6:]:
            role = "Teacher" if turn["role"] == "teacher" else "You (student)"
            history_text += f"\n{role}: {turn['text']}"

    system = f"""You are a student who initially believes:
"{misconception}"

Respond naturally as a confused student. Update your beliefs gradually when 
the teacher makes good points. Keep responses to 1-3 sentences. Be conversational.
Never break character. Do not repeat the teacher's words back verbatim.

Conversation so far:{history_text if history_text else ' (just started)'}"""

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": teacher_utterance},
            ],
            temperature=temperature,
            max_tokens=120,
        )
        response = (completion.choices[0].message.content or "").strip()
        return response if response else "I'm not sure I understand."
    except Exception as e:
        return f"[Student error: {str(e)[:60]}]"


def estimate_belief_score(student_response, misconception, correct_answer, previous_belief):
    stop_words = {
        "i", "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "to", "of", "and", "or", "in", "it", "that", "this", "my", "me",
        "you", "they", "we", "do", "does", "not", "no", "yes", "but",
    }

    def words(text):
        return set(re.findall(r"[a-z]+", text.lower())) - stop_words

    student_words = words(student_response)
    correct_words = words(correct_answer)
    misconception_words = words(misconception)

    correct_overlap = len(student_words & correct_words) / max(len(correct_words), 1)
    misconception_overlap = len(student_words & misconception_words) / max(len(misconception_words), 1)

    delta = (correct_overlap - misconception_overlap) * 0.25
    new_belief = previous_belief + delta
    # Clamp to (0.001, 0.999) to ensure strictly between 0 and 1
    clamped = max(0.001, min(0.999, new_belief))
    return round(clamped, 3)


def run_probe(probe_question, expected_keywords, student_history, misconception, correct_answer, seed=42):
    client = _get_client()
    history_text = "\n".join([
        f"{'Teacher' if t['role'] == 'teacher' else 'You'}: {t['text']}"
        for t in student_history[-4:]
    ])
    probe_prompt = f"""You are a student who has been in a lesson. Answer briefly:
"{probe_question}"

Recent lesson:
{history_text}

Answer in 1-2 sentences only."""

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": probe_prompt}],
            temperature=0.0,
            max_tokens=80,
            seed=seed,
        )
        answer = (completion.choices[0].message.content or "").lower()
    except Exception:
        return 0.01  # Strictly > 0

    matched = sum(1 for kw in expected_keywords if kw.lower() in answer)
    ratio = matched / max(len(expected_keywords), 1)

    if ratio >= 0.5:
        return 0.99  # Strictly < 1
    elif ratio >= 0.25:
        return 0.5
    else:
        return 0.01  # Strictly > 0