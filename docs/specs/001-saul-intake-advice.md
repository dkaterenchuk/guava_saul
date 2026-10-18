# Spec 001: Saul intake + guidance agent (hackathon demo)

- **Status:** in progress
- **Owner:** Jayesh
- **Plan:** `plan.md`, `agent-idea.md`

## Problem
A caller in a stressful legal situation phones in, tells their story, and wants to know what to do and not do next. The demo agent (Saul Goodman & Associates, a fictional firm) runs intake until the story is complete, confirms it, then gives general do/don't guidance and the options available with pros and cons. The caller can interrupt with "why?" at any point.

## Scope
- Inbound voice via Guava (phone, WebRTC, local mic) plus text chat and automated roleplay for testing.
- Phases as Guava tasks driven by deterministic code: greet, intake, confirm, advice, wrap, plus safety and handoff side paths.
- Advice generated once per call as structured JSON by Claude (fallback: Guava server LLM, then built-in generic guidance).

## Out of scope (v1 demo)
- Attorney-approved playbooks (Tier 2). This demo gives *general* guidance only and always points to a licensed lawyer.
- Jurisdiction-specific legal information and a sourced corpus (S4).
- A real attorney transfer line. Handoff collects a callback number.

## Done criteria
- [x] First turn discloses AI + recording + demo, verbatim, before any LLM turn (S1).
- [x] Safety scan runs on every caller utterance in code, not the LLM, and interrupts intake (S2).
- [x] Story-complete is deterministic: every required field filled (Guava task completion).
- [x] Deadline mentioned -> read back and confirmed before guidance (S6, C1).
- [x] Caller can ask for a person at any time and gets a callback flow (C4).
- [x] Advice never predicts outcomes; "talk to a licensed lawyer" is always an option; call ends with recap + disclaimer (C6).
- [x] Unit tests pass offline. Roleplay scenarios in `saul/scenarios.py` pass against Guava.
- [x] `compliance-reviewer` run on the diff (2026-10-17). Verdict: FAIL on policy scope (below); self-contained fixes applied.

## Compliance review findings (2026-10-17)

Applied in code:
- Fallback text had a guarantee ("nothing you say gets used against you") and a prediction ("waiting only gets worse"). Reworded.
- Safety signals were deduplicated for the whole call. Now only suppressed while the safety task is active, so a second danger statement re-escalates.
- A summary confirmation of "no" with no correction, or a second "no", now goes to attorney callback instead of advice (C1, upl "unsure of key facts").
- Advice delivery no longer overwrites a safety or handoff task that started while advice was being generated.
- An `active_arrest` signal always ends in handoff, never resumes intake (escalation.md: referral, no case analysis).
- "Get me a person" is detected in code on every caller utterance with a broader pattern (C4). "Are you a bot?" no longer triggers a handoff.
- Policy guard: generated advice is regex-scanned for outcome, strength, guarantee, and statute language; on any hit the built-in fallback is used instead.
- Logs no longer contain caller text or field values. Full dumps only with `SAUL_DEBUG_SYNTHETIC=1`, intended for roleplay runs.
- Child-safety script now gives the Childhelp hotline number. `on_question` is phase-aware during safety and handoff.

Left as decisions for the team (not applied):
- **B1 (core):** advice phase is off-playbook guidance on criminal matters, which `upl-boundaries.md` routes to Tier 3. Reviewer's fix: deterministic `tier_for(case)` that hands off criminal/deadline cases and keeps only Tier 1 information. Keeping the advice phase for the demo needs an ADR with founder sign-off and should not run on `--phone` with real callers.
- **B3:** no supported-jurisdiction gate (S5). Reviewer's fix: `SUPPORTED_STATES` allowlist, hand off outside it.
- **B4:** advice and the arrest-rights script are unsourced (S4). Needs a `docs/sources/` entry or removal.
- **B6 / W6:** no review-queue record for advised calls (S8) and no case summary persisted for the callback attorney. Both need a storage decision (gitignored `data/calls/`).
- **W4:** court date is free text, so the 7-day handoff trigger can't be computed. Reviewer's fix: separate `court_date` date field.
- **W9:** eval scenarios encode recommendations as passes; re-tag after B1 is decided.
- **N3 / N6:** record the implicit-consent choice in `recording-consent.md`; the departure from ADR 0001 needs its own ADR.

## Known policy tension
`docs/compliance/upl-boundaries.md` routes criminal matters to Tier 3 (hand off) and allows recommendations only inside an approved playbook. The demo's advice phase gives general guidance for criminal scenarios. This is a deliberate hackathon-demo scope choice, recorded here so it isn't mistaken for policy. Before any real caller: either write and get a playbook approved, or restrict the advice phase to Tier 1 information plus handoff.
