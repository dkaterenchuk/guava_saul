"""The case file: the intake checklist and the story-complete check.

Story-complete detection is deterministic: Guava marks the intake task complete only when every
required Field has a value. The LLM phrases the questions; code decides when intake is done.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import guava

# Keys in the order the agent should try to fill them. Guava fills any of these from the
# caller's free narrative first, then asks only for what's still missing.
REQUIRED_KEYS = [
    "state",
    "what_happened",
    "when_where",
    "parties_involved",
    "police_contact",
    "charges_or_court_dates",
    "statements_already_made",
    "evidence_witnesses",
    "caller_goal",
]

POLICE_CONTACT_CHOICES = ["none", "questioned", "cited", "arrested"]


def intake_fields() -> list[guava.Field]:
    """The intake checklist. One question per turn; Guava skips fields already answered."""
    return [
        guava.Field(
            key="state",
            question="Which state are you in?",
            description="The US state the caller is in. Needed before any guidance.",
        ),
        guava.Field(
            key="what_happened",
            description="The core incident, summarized in one or two plain sentences (not a word-for-word transcript).",
        ),
        guava.Field(
            key="when_where",
            description="When it happened and where, in plain words (for example 'last Friday night, outside a bar in Pasadena').",
        ),
        guava.Field(
            key="parties_involved",
            description="Who else was involved: other people, a store, a landlord, police. No need for full names.",
        ),
        guava.Field(
            key="police_contact",
            description="Whether police have been involved so far: none, questioned, cited (a ticket or citation), or arrested.",
            field_type="multiple_choice",
            choices=POLICE_CONTACT_CHOICES,
        ),
        guava.Field(
            key="charges_or_court_dates",
            description="Any charges, notices, court dates, or deadlines so far. If none yet, record 'none yet'. "
            "If there is a date, read it back and confirm it.",
        ),
        guava.Field(
            key="statements_already_made",
            description="What the caller has already said about this to police, to the other party, or online, if anything.",
        ),
        guava.Field(
            key="evidence_witnesses",
            description="Any video, texts, receipts, documents, or people who saw what happened.",
        ),
        guava.Field(
            key="caller_goal",
            description="What outcome the caller is hoping for or most worried about.",
        ),
    ]


@dataclass
class CaseFile:
    state: str = ""
    what_happened: str = ""
    when_where: str = ""
    parties_involved: str = ""
    police_contact: str = ""
    charges_or_court_dates: str = ""
    statements_already_made: str = ""
    evidence_witnesses: str = ""
    caller_goal: str = ""
    corrections: list[str] = field(default_factory=list)

    @classmethod
    def from_call(cls, call: guava.Call) -> "CaseFile":
        values = {k: _as_text(call.get_field(k)) for k in REQUIRED_KEYS}
        return cls(**values)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaseFile":
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        corrections = known.pop("corrections", None) or []
        if isinstance(corrections, str):
            corrections = [corrections]
        return cls(**known, corrections=list(corrections))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def missing(self) -> list[str]:
        return [k for k in REQUIRED_KEYS if not getattr(self, k).strip()]

    def is_complete(self) -> bool:
        return not self.missing()

    def has_deadline(self) -> bool:
        text = self.charges_or_court_dates.lower().strip()
        return bool(text) and text not in {"none", "none yet", "no", "nothing", "nothing yet", "n/a"}

    def summary_text(self) -> str:
        """Three or four spoken sentences for the read-back (CONFIRM phase)."""
        police = {
            "none": "Police haven't been involved yet",
            "questioned": "Police questioned you",
            "cited": "You were cited",
            "arrested": "You were arrested",
        }.get(self.police_contact, "Police involvement is unclear")
        deadline = (
            f"So far: {_clean(self.charges_or_court_dates)}."
            if self.has_deadline()
            else "No charges or court dates yet."
        )
        c = _clean
        parts = [
            f"Here's what I've got. {c(self.when_where)}, in {c(self.state)}: {c(self.what_happened)}.",
            f"Involved: {c(self.parties_involved)}. {police}. {deadline}",
            f"You've said this much to others: {c(self.statements_already_made)}. Evidence and witnesses: {c(self.evidence_witnesses)}.",
            f"And what you want out of this is: {c(self.caller_goal)}.",
        ]
        if self.corrections:
            parts.append("Corrections you gave me: " + " ".join(self.corrections))
        return " ".join(p.strip() for p in parts)


def _clean(value: str) -> str:
    """Trim whitespace and trailing punctuation so values slot into a sentence."""
    return (value or "").strip().rstrip(".!, ")


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        # date / datetime fields come back as dicts
        y, m, d = value.get("year"), value.get("month"), value.get("day")
        if y and m and d:
            return f"{y}-{m:02d}-{d:02d}"
        return " ".join(str(v) for v in value.values())
    return str(value).strip()
