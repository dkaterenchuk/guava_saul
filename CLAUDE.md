# guava_saul

Voice agent for legal help. A caller phones in, and a Guava voice agent runs a structured intake to understand their situation. It then works in tiers (ADR 0001): **0** escalate safety issues, **1** give sourced legal information, **2** resolve basic cases using attorney-approved playbooks, **3** hand off to legal counsel. The goal is to help the caller, and resolve what's safe to resolve. Failure modes here hurt real people, so safety rules outrank features.

> Shared file. Everyone edits it through PRs. Keep it under ~2.5k tokens. If it bloats, rewrite it; don't append. Personal preferences go in `CLAUDE.local.md` (gitignored).

## Where things live

| Need | Read |
|---|---|
| What we're building and for whom | `docs/product/vision.md` |
| Product rules (testable) | `docs/product/principles.md` |
| What the agent may say at each tier | `docs/compliance/upl-boundaries.md` |
| Tier model and supervision | `docs/decisions/0001-tiered-guidance.md` |
| When to hand off or escalate | `docs/compliance/escalation.md` |
| Call recording and AI disclosure | `docs/compliance/recording-consent.md` |
| PII, transcripts, retention | `docs/compliance/data-handling.md` |
| Voice persona and handling unclear speech | `docs/voice/` |
| Intake flows + resolution playbooks per practice area | `docs/voice/intake-flows/` |
| Guava SDK facts we've verified | `docs/integrations/guava.md` |
| System design | `docs/ARCHITECTURE.md` |
| Settled decisions (don't re-litigate) | `docs/decisions/` |
| Feature specs and per-task logs | `docs/specs/`, `docs/worklog/` |
| Evals (the definition of done) | `evals/` |

**Read before acting:** for any change to prompts, intake flows, agent behavior, or caller-facing text, first read `principles.md` and `upl-boundaries.md`.

## Workflow

1. **Non-trivial work starts in Plan Mode** and with a spec at `docs/specs/NNN-slug.md` (copy `_TEMPLATE.md`). Fill in the done criteria before writing code.
2. Keep a running log at `docs/worklog/NNN-slug.md`: what was done, what's next, open questions. Update it before ending a session, so the next session can resume.
3. Any change to caller-facing behavior needs a new or updated eval scenario in `evals/scenarios/`.
4. Before calling caller-facing work done, run the `compliance-reviewer` subagent on the diff.
5. A decision that would be costly to reverse gets an ADR in `docs/decisions/`.

## Commands

<!-- Fill in once the Python project is initialized. -->
- Lint: `TBD`
- Test: `TBD`
- Evals: `TBD`

## Never

- Never commit real caller data: audio, transcripts, phone numbers, names. Use synthetic data only. A hook enforces this for `data/raw/` and audio files.
- Never let the agent advise outside an attorney-approved playbook, predict case outcomes, or guarantee results (see `upl-boundaries.md`).
- Never write, activate, or edit a playbook's guidance and set `approved_by` yourself. Draft it, and a licensed attorney approves it.
- Never let the LLM decide the tier. Tier routing and playbook eligibility are deterministic code.
- Never remove or weaken AI disclosure, recording notice, or escalation paths without an ADR.
- Never add a new practice area or jurisdiction without an intake flow, eval scenarios, and a sources list.
- Never act on a low-confidence transcription of a name, date, amount, or deadline. Read it back and confirm.
- Never invent Guava SDK behavior. If it isn't in `docs/integrations/guava.md`, check the official docs and record what you find.

## Lessons

Mistakes Claude made that we don't want repeated. Format: `[area] Mistake — Do this instead.` Add one when a mistake repeats, and prune entries that no longer apply.

<!-- none yet -->
