import json

import structlog
from openai import AsyncOpenAI

from src.config import settings

logger = structlog.get_logger()

client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT_CHECK = """You are an Uzbek language tutor checking student answers.
The student is learning Uzbek from scratch (Russian-speaking).

CRITICAL RULES — when in doubt, mark as CORRECT:
- Accept ANY case: "xayrli tong", "Xayrli Tong", "XAYRLI TONG" — all correct
- Accept transliteration variants: salom, Salom, салом — all correct
- Accept minor typos if the word is recognizable (1-2 wrong letters)
- Accept both Latin and Cyrillic Uzbek script
- Accept with or without punctuation (!, ?, .)
- Accept with or without extra spaces
- If the meaning matches the expected answer — it is CORRECT
- For open_translate: student must write in target language, not source
- For fill_blank: only the missing word matters, ignore case
- For dialog_reply: any contextually appropriate response is correct
- Be encouraging, never harsh
- NEVER mark a correct answer as wrong — this destroys student motivation

Respond ONLY with valid JSON (no markdown):
{
  "correct": true/false,
  "score": 0.0-1.0,
  "feedback": "short encouraging explanation in Russian",
  "corrected": "correct answer if wrong, null if correct"
}"""

SYSTEM_PROMPT_DIALOG = """You are a friendly Uzbek person having a conversation.
Speak simple Uzbek (A1 level). After each reply, add a Russian translation in parentheses.
Keep replies short (1-2 sentences).
If the student makes mistakes, gently continue the conversation — don't correct explicitly."""


async def check_answer(
    exercise_type: str,
    prompt: str,
    user_answer: str,
    answer_context: str,
) -> dict:
    """Check student's answer using LLM. Returns {correct, score, feedback, corrected}."""
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_CHECK},
                {
                    "role": "user",
                    "content": (
                        f"Exercise type: {exercise_type}\n"
                        f"Question: {prompt}\n"
                        f"Expected answer: {answer_context}\n"
                        f"Student wrote: {user_answer}\n\n"
                        f"Is this correct? Respond with JSON only."
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=200,
        )

        content = response.choices[0].message.content or "{}"
        # Strip markdown code block if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]

        result = json.loads(content)

        return {
            "correct": result.get("correct", False),
            "score": result.get("score", 0.0),
            "feedback": result.get("feedback", ""),
            "corrected": result.get("corrected"),
        }

    except Exception as e:
        # Log type only — error message can echo back the request body,
        # which embeds answer_context. Caller translates to HTTP 503.
        logger.error("llm_check_failed", error_type=type(e).__name__)
        raise


async def checkpoint_dialog(
    scenario: str,
    user_message: str,
    history: list[dict],
) -> str:
    """AI conversation for checkpoint role-play."""
    safe_history = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_DIALOG + f"\n\nScenario: {scenario}",
        },
        *safe_history,
        {"role": "user", "content": user_message},
    ]

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.7,
            max_tokens=150,
        )
        return response.choices[0].message.content or ""

    except Exception as e:
        logger.error("llm_dialog_failed", error=str(e))
        return "Kechirasiz, xatolik yuz berdi. (Извините, произошла ошибка.)"
