# Architecture (draft)

```
Caller ──phone──▶ Guava (telephony, ASR, TTS, turn-taking)
                      │ WebSocket
                      ▼
               Our backend (Python)
               ├─ Safety layer      escalation detection runs on every turn, before anything else
               ├─ Intake engine     drives the flow in docs/voice/intake-flows/, fills the case summary
               ├─ Tier router       decides Tier 1/2/3 from intake fields + playbook eligibility (S7)
               ├─ Legal info layer  retrieval over the vetted corpus, cited answers only (S4)
               ├─ Playbook engine   runs approved playbooks only; loads by ID + version
               ├─ Policy guard      checks outgoing replies against the active tier/playbook (S3)
               ├─ Handoff           routes to legal counsel with the case summary
               └─ Review queue      resolved calls → async attorney review (S8)
```

## Key choices (each becomes an ADR when decided)
- **Retrieval over fine-tuning for legal content.** It's auditable, citable, and updatable when the law changes. Fine-tuning, if used at all, is for tone or format, not legal facts. *(Proposed.)*
- **Safety layer runs first on every turn**, independent of the LLM's reply. *(Proposed.)*
- **Tier routing is deterministic code**, not the LLM's judgment. The LLM phrases the guidance; code decides whether guidance is allowed. *(Proposed.)*
- **Prompts and flows are versioned files in the repo**, not strings scattered through code. One source of truth.

## Layout (when code starts)
```
src/guava_saul/{safety,intake,legal_info,policy,handoff}/
prompts/            # versioned system prompts
corpus/             # source manifests (metadata only; licensed content stays out of git)
evals/
```
