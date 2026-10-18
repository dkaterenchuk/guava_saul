# Worklog 001: Saul intake + guidance agent

## 2026-10-17
**Done**
- Verified the Guava SDK (0.48.0) programming model: `guava.Agent` + `Call` with tasks/fields; hosted dialog model does the talking. `CallController` is deprecated. Recorded in `docs/integrations/guava.md`.
- Built `saul/`: agent (phases as tasks), case file (9 required fields), deterministic safety layer, advice schema + chunking + fallback, LLM wrappers (Claude -> Guava server LLM -> fallback), roleplay scenarios, CLI.
- 18 offline unit tests passing (`.venv/bin/python -m pytest -q`).
- `script.md` for manual testing. Eval scenarios added under `evals/scenarios/saul-*.md`.

- Live roleplays against Guava: `dui` PASS, `safety` PASS, `human` fixed after first FAIL (hosted model kept asking intake questions; handoff is now triggered in code from `on_caller_speech`).
- Compliance review run; findings and what was applied are in spec 001.

**Next**
- Team decision on spec 001 B1 (advice phase vs. Tier 3 handoff for criminal matters) and B3 (jurisdiction allowlist). Needs an ADR either way.
- Add `court_date` as a real date field so the 7-day urgency rule can run in code.
- Decide where handoff summaries and review records live (`data/calls/`, gitignored).

**Known limitation**
- Safety escalation races the hosted model by up to one turn: our `set_task("safety")` is sent within the same second the signal is heard, but a reply already being generated can still contain one more intake question. Seen once in two roleplay runs. An immediate `send_instruction("STOP...")` is now sent alongside the task switch. If it still slips, that is a platform-level limit worth raising with Guava (an "interrupt current reply" command).

**Open questions**
- Does Guava expose ASR confidence per field? Not seen in the SDK. Confirmation is done by read-back for now.
- `on_question` fires only when the hosted model can't answer from `add_info` context. Whether "why?" interruptions route there or are answered inline by the hosted model needs checking in live calls.
