---
name: design-intake-flow
description: Design or revise a voice intake flow for a practice area and jurisdiction. Use when someone says "Flow:" or asks to add or change intake questions.
---

1. Read `docs/voice/` (all of it), `docs/compliance/upl-boundaries.md`, and `docs/compliance/escalation.md`.
2. Copy `docs/voice/intake-flows/_TEMPLATE.md` to `<area>-<state>.md`.
3. Design the fields as the case summary an attorney would need first. Minimum necessary (D1).
4. Write every question as spoken, plain language. One question per turn (C2). Mark the critical fields to confirm back (C1).
5. List the corpus sources for every piece of information the agent may give. With no source, the agent doesn't say it (S4).
6. For basic, high-volume case types, draft Tier 2 playbooks: tight eligibility criteria, guidance steps with sources, and exit conditions. Make eligibility conservative. A wrongful resolution is worse than an unnecessary handoff.
7. Create eval scenarios covering at least: a fluent caller, an unclear-speech caller, an advice-seeking caller off-playbook, a safety signal mid-flow, and for each playbook, one eligible case and one near-miss that fails exactly one criterion.
8. Set status to `draft` and leave `approved_by` empty. Only a licensed attorney fills it in.
