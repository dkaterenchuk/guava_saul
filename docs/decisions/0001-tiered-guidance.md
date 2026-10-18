# 0001: Tiered guidance. The AI advises within attorney-approved playbooks and hands off everything else.

- **Status:** proposed (needs founder sign-off, plus counsel sign-off on the supervision structure)
- **Date:** 2026-10-17

## Context
The goal is for the AI to resolve many basic cases on its own, not only do intake. But an AI applying law to a caller's facts and recommending action is exactly what UPL rules target, and wrong advice causes real harm (missed deadlines, forfeited rights). A disclaimer alone doesn't make advice permissible. Attorney supervision, plus a business structure that allows it, is what makes it defensible.

## Decision
Every turn falls into one of four tiers:

| Tier | What the agent does | When |
|---|---|---|
| 0 Escalate | Safety routing (`escalation.md`) | Any danger signal. Overrides everything. |
| 1 Inform | General legal information, sourced | Any supported jurisdiction |
| 2 Guide | Recommends next steps from an **attorney-approved playbook** | The case matches a playbook and **all** of its eligibility criteria are met |
| 3 Hand off | Routes to legal counsel with the case summary | Off-playbook, an eligibility criterion fails, high stakes, or the caller asks |

Supervision:
- Each playbook is written or approved by a licensed attorney for its jurisdiction, versioned in the repo, and records who approved it and when.
- Resolved (Tier 2) calls go into an async attorney review queue, sampled at first and then risk-weighted. Attorneys can follow up with the caller.
- Playbooks are allowlisted. The agent never improvises advice outside one.

## Alternatives rejected
- **Information only, no advice.** Safe, but resolves few cases. Rejected as too weak for the product goal.
- **Open-ended AI advice with a disclaimer.** UPL exposure and harm risk, and the advice can't be audited.
- **Attorney approves every answer live.** Too slow for a phone call.

## Consequences
- The product's scope equals its playbook library. Growth means writing more playbooks and evals, not loosening the prompts.
- Recruiting attorneys (for playbook approval and the review queue) is on the critical path.
- **Open, for counsel:** the legal structure (law-firm partnership, Utah sandbox, Arizona ABS, or other) and whether callers get an attorney-client relationship.
