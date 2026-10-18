# Vision

## Problem
Most people facing a legal problem (eviction notice, unpaid wages, a court date) can't afford a lawyer for a first conversation, don't know which kind of help they need, and freeze. Legal aid hotlines have long waits and spend most of their staff time on intake.

## Product
A phone line anyone can call. A voice agent built on Guava:
1. **Listens and adapts.** It handles stressed, accented, or unclear speech, interruptions, and noisy lines.
2. **Runs structured intake.** It asks questions to understand the caller's situation: issue type, jurisdiction, deadlines, parties, documents they have.
3. **Resolves basic cases itself.** For common, well-defined situations, the agent gives guidance from attorney-approved playbooks. For anything else, it gives sourced legal information in plain language.
4. **Hands off the rest.** Complex, high-stakes, or off-playbook cases go to legal counsel with the case summary attached. Resolved calls are reviewed by attorneys afterwards.

## Caller
Someone in a stressful legal situation. They may be non-native speakers, calling from a phone with a poor connection, and unfamiliar with legal terms. What they need to discover: what kind of problem they have, how urgent it is, and who can actually help.

## Wedge (open, decide before building)
Start with **one practice area in one state**. Candidates: tenant/eviction, wage theft, immigration intake. Evals, the source corpus, and compliance review are only tractable with a narrow scope. Record the choice as an ADR.

## Non-goals (v1)
- Representing callers, filing documents, or forming an attorney-client relationship.
- Predicting outcomes, or advising outside an approved playbook.
- Covering every practice area or jurisdiction.
- Replacing attorneys. The product makes attorney time go further.

## Success (draft)
- **Resolution rate:** the share of calls resolved at Tier 2 with no handoff, *and* upheld on attorney review. A resolution that gets overturned on review counts against us.
- The caller leaves with a correct, sourced understanding of their situation and one concrete next step.
- Intake summaries are good enough that a receiving attorney doesn't need to re-ask the basics.
- Zero safety-critical misses in the eval suite (escalation, disclosure, UPL boundary).
