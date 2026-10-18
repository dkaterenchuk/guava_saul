"""Deterministic safety layer. Runs on every caller utterance, before anything else (principle S2).

Keyword rules, not an LLM, so escalation never depends on model judgment. False positives cost a few
seconds; a miss can cost far more, so the patterns err toward matching (docs/compliance/escalation.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

DV_HOTLINE = "1-800-799-7233"
CRISIS_LINE = "988"
CHILD_HOTLINE = "1-800-422-4453"


@dataclass(frozen=True)
class SafetySignal:
    category: str  # emergency | self_harm | domestic_violence | child | active_arrest
    matched: str


_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "self_harm",
        re.compile(
            r"\b(kill myself|end it all|end my life|suicid\w*|don'?t want to (live|be here|be alive)|"
            r"hurt myself|not worth living|better off dead)\b",
            re.I,
        ),
    ),
    (
        "child",
        re.compile(
            r"\b(my (kid|kids|child|children|son|daughter|baby)\b.{0,40}\b(hurt|danger|unsafe|hit|hitting|abus\w*|threat\w*))|"
            r"\b(hurt|hit|hitting|abus\w*|threat\w*)\b.{0,40}\b(my (kid|kids|child|children|son|daughter|baby))\b",
            re.I,
        ),
    ),
    (
        "domestic_violence",
        re.compile(
            r"\b(my (husband|wife|partner|boyfriend|girlfriend|ex|spouse)|\bhe|\bshe)\b.{0,60}"
            r"\b(hurt me|hurts me|hit me|hits me|beat me|beats me|choked? me|threaten\w* me|going to kill me|will kill me|gonna kill me)\b"
            r"|\b(afraid|scared|terrified) (of|he'?ll|she'?ll|he will|she will)\b.{0,30}\b(hurt|hit|kill|come back|comes back|gets back|get back|home)\b"
            r"|\b(hurt me|kill me)\b.{0,30}\b(if i|when he|when she|before he|before she)\b",
            re.I,
        ),
    ),
    (
        "emergency",
        re.compile(
            r"\b(bleeding|not breathing|unconscious|overdos\w*|has a (gun|knife)|got a (gun|knife)|pulled a (gun|knife)|"
            r"(he|she|they)('s| is| are)? (here|outside|at the door|breaking in|coming in)( right)? now|"
            r"right now.{0,20}(hurt|attack|hit)|"
            r"(someone|somebody)('s| is)? (hurt|dying|attacking))\b",
            re.I,
        ),
    ),
    (
        "active_arrest",
        re.compile(
            r"\b((being|getting) arrested|arresting me|cops are (here|at my door|outside)|police are (here|at my door|outside)|"
            r"(they|cops|police)('re| are)? (cuffing|handcuffing|detaining) me|i'?m (in|at) (the )?(back of a (cop|police) car|a (holding )?cell)|"
            r"(detained|in custody|being booked) right now)\b",
            re.I,
        ),
    ),
]


def scan(utterance: str) -> SafetySignal | None:
    """Return the first danger signal found in the utterance, or None."""
    text = utterance or ""
    for category, pattern in _PATTERNS:
        m = pattern.search(text)
        if m:
            return SafetySignal(category=category, matched=m.group(0))
    return None


def safety_script(signal: SafetySignal) -> str:
    """Verbatim first response for each signal (docs/compliance/escalation.md)."""
    return {
        "emergency": (
            "Stop. If someone is in danger or hurt right now, hang up and call 911. "
            "That comes before anything else. Are you safe to keep talking?"
        ),
        "self_harm": (
            "I want to pause on the legal stuff for a second, because what you just said matters more. "
            f"You can call or text {CRISIS_LINE}, the Suicide and Crisis Lifeline, any time, and they will pick up. "
            "Are you safe right now?"
        ),
        "domestic_violence": (
            "Let me stop and make sure you're okay. "
            f"If you're in danger right now, call 911. The National Domestic Violence Hotline is {DV_HOTLINE}. "
            "Is it safe for you to keep talking to me right now?"
        ),
        "child": (
            "I need to pause. If a child is in danger right now, call 911. "
            f"The Childhelp hotline is {CHILD_HOTLINE}, any time. Is the child safe right now?"
        ),
        "active_arrest": (
            "Okay, listen carefully. You have the right to stay silent and the right to a lawyer. "
            "Say clearly: 'I want a lawyer, and I'm not answering questions.' Then stop talking. Don't resist, don't argue. "
            "Are you able to keep talking to me?"
        ),
    }[signal.category]


def safety_followup_objective(signal: SafetySignal) -> str:
    return (
        "A safety concern came up. Stay calm and warm. Do not continue the legal intake until you've checked whether "
        "the caller is safe right now. If they say they are not safe, repeat the emergency number and the hotline, "
        "and tell them to call it now. If they say they are safe and want to continue, record that. "
        "Do not minimize what they said."
    )


# Deterministic intent helpers for the handoff and done paths (no LLM).
_HUMAN_RE = re.compile(
    r"\b(want|need|get me|give me|speak|talk|connect me|transfer me|put me|through to|can i (have|get))\b.{0,25}"
    r"\b(a |an |the |some )?(real |actual |live |human )?(person|human|lawyer|attorney|someone|somebody|operator|representative)\b"
    r"|\b(real|actual|live) (person|human)\b",
    re.I,
)
_DONE_RE = re.compile(
    r"\b(that'?s (all|it|everything)|i'?m (done|good|all set)|no more questions|nothing else|we'?re done|thanks,? (bye|that's all))\b",
    re.I,
)


def wants_human(utterance: str) -> bool:
    return bool(_HUMAN_RE.search(utterance or ""))


def is_done(utterance: str) -> bool:
    return bool(_DONE_RE.search(utterance or ""))
