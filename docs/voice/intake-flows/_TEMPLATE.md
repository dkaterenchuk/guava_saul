# Intake flow: <practice area> / <jurisdiction>

- **Status:** draft | reviewed-by-counsel | live
- **Corpus sources:** list the vetted sources the agent may cite for this flow.
- **Eval scenarios:** `evals/scenarios/<...>`

## Entry signals
Phrases or facts that route a call into this flow.

## Safety checks
Flow-specific escalation triggers, on top of `compliance/escalation.md`.

## Fields (the case summary)
| Field | Type | Required | Confirm back? | Question (plain language) |
|---|---|---|---|---|
| jurisdiction_state | enum | yes | yes | "What state are you in?" |
| deadline_date | date | if any | yes | "Is there a date on the notice, or a court date?" |

## Branches
Which follow-up questions depend on which answers.

## Information the agent may give (Tier 1)
Allowed explanations, each tied to a corpus source.

## Playbooks (Tier 2)
One block per basic case type the agent may resolve. A playbook without `approved_by` is inactive.

### Playbook: <id> (e.g. tenant-deposit-return-ca)
- **Version:** 1
- **approved_by:** <attorney name, bar #, state> · **approved_on:** YYYY-MM-DD
- **Eligibility (all must be confirmed):**
  - [ ] criterion, e.g. "moved out more than 21 days ago"
  - [ ] criterion, e.g. "amount under $X"
- **Guidance:** the steps the agent may recommend, in plain spoken language, each with a source.
- **Exit to Tier 3 if:** conditions that end the playbook mid-call.
- **Review flags:** facts that put the call at the front of the attorney review queue.

## Exit / next step
Which handoff or resource goes with which situation.
