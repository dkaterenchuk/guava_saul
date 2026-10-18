"""LLM calls. Provider order: Claude (if ANTHROPIC_API_KEY) -> Guava server LLM -> built-in fallback.

Only two calls exist:
- generate_advice(case): one-shot, structured JSON.
- answer_question(case, advice, question): short spoken answer for "why?" interruptions.
"""
from __future__ import annotations

import json
import logging
import os

from .advice import Advice, check_advice, fallback_advice, find_why
from .case_file import CaseFile
from .prompts import ADVICE_SYSTEM, NO_ANSWER, QA_SYSTEM

logger = logging.getLogger("saul.llm")

DEFAULT_MODEL = "claude-opus-5-5"


def model_id() -> str:
    return os.environ.get("SAUL_MODEL") or DEFAULT_MODEL


def _claude_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def generate_advice(case: CaseFile) -> tuple[Advice, str]:
    """Return (advice, provider). Never raises; the fallback always works."""
    case_json = json.dumps(case.to_dict(), indent=2)
    schema = Advice.model_json_schema()

    advice: Advice | None = None
    provider = "fallback"
    if _claude_available():
        try:
            advice, provider = _claude_advice(case_json, schema), "claude"
        except Exception:
            logger.exception("Claude advice generation failed; trying Guava server LLM.")
    if advice is None:
        try:
            advice, provider = _guava_advice(case_json, schema), "guava"
        except Exception:
            logger.exception("Guava server LLM advice generation failed; using built-in fallback.")

    if advice is not None:
        hits = check_advice(advice)
        if hits:
            # Policy guard tripped: never speak predicted outcomes, guarantees, or statutes.
            logger.warning("policy guard rejected %s advice (%d banned phrases); using fallback", provider, len(hits))
            advice, provider = None, f"fallback-after-{provider}"

    return (advice or fallback_advice(case)), provider


def answer_question(case: CaseFile, advice: Advice | None, question: str) -> str:
    """Short spoken answer to a caller's follow-up. Never raises."""
    if advice is None:
        from .prompts import HOLD_THAT_THOUGHT

        return HOLD_THAT_THOUGHT

    if _claude_available():
        try:
            return _claude_answer(case, advice, question)
        except Exception:
            logger.exception("Claude QA failed; falling back to offline lookup.")

    why = find_why(advice, question)
    if why:
        return f"{why} Want me to keep going?"
    return NO_ANSWER


# ---------------------------------------------------------------------------
# Claude
# ---------------------------------------------------------------------------

def _claude_client():
    import anthropic

    return anthropic.Anthropic(timeout=60.0)


def _claude_advice(case_json: str, schema: dict) -> Advice:
    client = _claude_client()
    resp = client.messages.create(
        model=model_id(),
        max_tokens=4096,
        system=ADVICE_SYSTEM,
        messages=[{"role": "user", "content": f"Case file:\n{case_json}"}],
        output_config={"format": {"type": "json_schema", "schema": schema}, "effort": "medium"},
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined the request: {resp.stop_details}")
    text = "".join(b.text for b in resp.content if b.type == "text")
    return Advice.model_validate_json(text)


def _claude_answer(case: CaseFile, advice: Advice, question: str) -> str:
    client = _claude_client()
    user = (
        f"Case file:\n{json.dumps(case.to_dict(), indent=2)}\n\n"
        f"Guidance already given:\n{advice.model_dump_json(indent=2)}\n\n"
        f"Caller's question: {question}"
    )
    resp = client.messages.create(
        model=model_id(),
        max_tokens=512,
        system=QA_SYSTEM,
        messages=[{"role": "user", "content": user}],
        output_config={"effort": "low"},
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined the request: {resp.stop_details}")
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    return text or NO_ANSWER


# ---------------------------------------------------------------------------
# Guava server LLM (no extra key needed once `guava login` has run)
# ---------------------------------------------------------------------------

def _guava_advice(case_json: str, schema: dict) -> Advice:
    from guava.helpers.llm import generate

    prompt = f"{ADVICE_SYSTEM}\n\nCase file:\n{case_json}\n\nRespond with JSON only."
    raw = generate(prompt, json_schema=schema)
    return Advice.model_validate_json(raw)
