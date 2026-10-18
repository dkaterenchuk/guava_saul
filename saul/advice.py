"""Advice schema, spoken chunking, and the no-LLM fallback.

The advice JSON is generated once (saul/llm.py) and stored on the call. Chunks are what the agent
speaks; the `why` fields are what the agent reads from when the caller interrupts with "why?".
"""
from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field

from .case_file import CaseFile


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AdviceItem(_Strict):
    action: str = Field(description="One spoken sentence: what to do or not do.")
    why: str = Field(description="One or two plain sentences on why.")


class Option(_Strict):
    name: str = Field(description="Short name of the path, e.g. 'Stay quiet and get a lawyer first'.")
    pros: list[str] = Field(description="1-3 short spoken pros.")
    cons: list[str] = Field(description="1-3 short spoken cons.")
    saul_take: str = Field(description="One sentence: which path people usually consider first and why. No promises.")


class Advice(_Strict):
    do: list[AdviceItem] = Field(description="Up to 3 things to do or say now.")
    dont: list[AdviceItem] = Field(description="Up to 3 things not to do or say.")
    options: list[Option] = Field(description="2-3 realistic paths, one of them 'talk to a licensed lawyer first'.")
    top3: list[str] = Field(description="The three most important actions, each one short sentence.")


def advice_chunks(advice: Advice) -> list[str]:
    """Turn the advice JSON into short spoken chunks (about two sentences each)."""
    chunks: list[str] = []
    if advice.do:
        chunks.append("First, what to do. " + " ".join(_sentence(i.action) for i in advice.do[:3]))
    if advice.dont:
        chunks.append("Now, what not to do. " + " ".join(_sentence(i.action) for i in advice.dont[:3]))
    for idx, opt in enumerate(advice.options[:3], start=1):
        pros = "; ".join(p.strip().rstrip(".") for p in opt.pros[:3]) or "not much"
        cons = "; ".join(c.strip().rstrip(".") for c in opt.cons[:3]) or "not much"
        chunks.append(
            f"Option {idx}: {_sentence(opt.name)} The upside: {pros}. The downside: {cons}. {_sentence(opt.saul_take)}"
        )
    return [c.strip() for c in chunks if c.strip()]


def advice_notes(advice: Advice) -> dict:
    """Context handed to the voice agent so it can answer 'why?' from the same material."""
    return {
        "do": [{"action": i.action, "why": i.why} for i in advice.do],
        "dont": [{"action": i.action, "why": i.why} for i in advice.dont],
        "options": [o.model_dump() for o in advice.options],
        "top3": advice.top3,
        "rules": [
            "Never predict the outcome or say the case is strong or weak.",
            "Never promise a result.",
            "If a question needs a lawyer's judgment, say so and offer an attorney callback.",
        ],
    }


def find_why(advice: Advice, question: str) -> str | None:
    """Offline 'why?' lookup: pick the advice item whose action overlaps the question most."""
    q_words = _words(question)
    if not q_words:
        return None
    best: tuple[int, str] | None = None
    for item in [*advice.do, *advice.dont]:
        score = len(q_words & _words(item.action))
        if score and (best is None or score > best[0]):
            best = (score, item.why)
    for opt in advice.options:
        score = len(q_words & _words(opt.name))
        if score and (best is None or score > best[0]):
            best = (score, f"{opt.saul_take} Upside: {'; '.join(opt.pros)}. Downside: {'; '.join(opt.cons)}.")
    return best[1] if best else None


def fallback_advice(case: CaseFile) -> Advice:
    """Universal guidance that applies to almost any situation. Used when no LLM is reachable."""
    do: list[AdviceItem] = []
    if case.has_deadline():
        do.append(
            AdviceItem(
                action=f"Write down this date and do not miss it: {case.charges_or_court_dates}.",
                why="Missing a court date or deadline can create a whole new problem on top of the first one, like a warrant or losing the chance to respond.",
            )
        )
    do += [
        AdviceItem(
            action="Write down everything you remember about what happened, today, while it's fresh.",
            why="Memories fade fast and details matter. A written timeline helps any lawyer you talk to.",
        ),
        AdviceItem(
            action="Save every text, photo, receipt, and name of anyone who saw it.",
            why="Evidence disappears. Phones get wiped, footage gets overwritten, and people forget.",
        ),
        AdviceItem(
            action="Talk to a licensed lawyer before you talk to anyone else about it.",
            why="A lawyer can tell you what applies in your state and your situation. I can't.",
        ),
    ]
    dont = [
        AdviceItem(
            action="Don't talk to police or investigators about it without a lawyer present.",
            why="You have the right to stay silent. Anything you say can be used against you, even things that feel harmless.",
        ),
        AdviceItem(
            action="Don't post about it, text about it, or explain yourself to the other side.",
            why="Posts and messages get screenshotted and used as evidence. Explaining yourself rarely helps and often hurts.",
        ),
        AdviceItem(
            action="Don't sign anything or agree to anything until a lawyer has looked at it.",
            why="Signed statements and agreements are hard to undo.",
        ),
    ]
    options = [
        Option(
            name="Stay quiet and talk to a lawyer first.",
            pros=["Protects your rights", "Keeps you from saying something that could be used against you", "The lawyer can deal with the other side for you"],
            cons=["Costs money or takes time to find free legal aid", "Can feel like you're not doing anything"],
            saul_take="This is the path most people in your spot start with, because it keeps every other option open.",
        ),
        Option(
            name="Cooperate and explain your side yourself.",
            pros=["Feels proactive", "Can sometimes clear up a simple misunderstanding quickly"],
            cons=["Anything you say can be used against you", "You can't take it back", "You don't know what they already know"],
            saul_take="People usually hold off on this until a lawyer has told them it's safe.",
        ),
        Option(
            name="Wait and see what happens.",
            pros=["No cost right now"],
            cons=["Deadlines can pass without you knowing", "Evidence can disappear", "The other side keeps moving"],
            saul_take="Most people check with a lawyer before choosing to wait, because deadlines don't wait with you.",
        ),
    ]
    top3 = [a.action for a in do[:3]]
    return Advice(do=do[:3], dont=dont[:3], options=options, top3=top3)


# Policy guard: outcome predictions, guarantees, case-strength talk, and statute citations are
# never allowed at any tier (docs/compliance/upl-boundaries.md). Code checks, not the LLM.
_BANNED = re.compile(
    r"\b(you('ll| will) (win|lose|walk|be fine|be convicted|get off))\b"
    r"|\b(strong|weak|solid|airtight|open.and.shut) (case|claim|defense)\b"
    r"|\bguarantee\w*\b|\bwon'?t (lose|be convicted|be charged)\b"
    r"|\b(will|would|should) (be|get) (dismissed|dropped|thrown out|convicted|acquitted)\b"
    r"|\b(penal|vehicle|criminal) code\b|\bstatute\b|§|\b[A-Z][a-z]+ v\.? [A-Z][a-z]+\b",
    re.I,
)


def check_advice(advice: Advice) -> list[str]:
    """Return every string in the advice that contains banned language. Empty list means clean."""
    hits: list[str] = []
    for text in _all_strings(advice):
        if _BANNED.search(text):
            hits.append(text)
    return hits


def _all_strings(advice: Advice) -> list[str]:
    out: list[str] = []
    for item in [*advice.do, *advice.dont]:
        out += [item.action, item.why]
    for opt in advice.options:
        out += [opt.name, opt.saul_take, *opt.pros, *opt.cons]
    out += advice.top3
    return out


def _sentence(text: str) -> str:
    t = (text or "").strip()
    if t and t[-1] not in ".!?":
        t += "."
    return t


_STOP = {
    "the", "a", "an", "to", "and", "or", "of", "i", "you", "me", "my", "it", "is", "do", "don't", "dont", "not",
    "why", "what", "if", "can", "can't", "cant", "just", "should", "about", "that", "this", "they", "them",
}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z']+", (text or "").lower()) if w not in _STOP and len(w) > 2}
