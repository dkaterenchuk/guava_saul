# Escalation and handoff

> **Status: DRAFT.** Fill in real numbers and partner routes before any live call.

## Safety escalation (interrupts intake immediately)
| Signal | Action |
|---|---|
| Immediate danger, violence in progress, medical emergency | Tell the caller to hang up and call 911. Offer to stay on the line if the platform supports it. |
| Self-harm or suicidal statements | Give 988 (Suicide & Crisis Lifeline). Don't continue intake unless the caller asks. |
| Domestic violence | Give the DV hotline (1-800-799-7233). Check whether it's safe to keep talking. |
| A child in danger | Route to emergency services and the state child-protective line. |
| Caller says they're being arrested or detained right now | Give general rights information from the corpus plus a criminal or immigration defense referral. No case analysis. |

The agent errs toward escalating. A false positive costs a few seconds, and a missed signal can cost far more.

## Handoff to a human
Triggers: the caller asks for a person, no playbook matches, a playbook eligibility criterion fails or stays unknown, an always-hand-off category (see `upl-boundaries.md`), the agent is confused twice in a row, a deadline is within 7 days (provisional threshold), or the jurisdiction isn't supported.

A handoff always includes a case summary (the intake fields collected so far) so the caller doesn't have to repeat themselves (principle C5).

## Open
- [ ] Partner attorneys and orgs per launch jurisdiction.
- [ ] Hours coverage: what happens to a handoff after hours (callback queue?).
- [ ] Whether Guava supports warm transfer with context. Verify and record in `integrations/guava.md`.
