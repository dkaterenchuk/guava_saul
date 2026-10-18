# Guava: verified facts

**Rule:** only record things verified in the official docs or by running code, with a link and the date checked. Claude must not assume Guava behavior that isn't recorded here.

Official docs: https://goguava.ai (confirm the docs URL and the Python SDK repo).

## Unverified leads (from third-party listings, 2026-10-17). Verify each before relying on it.
- The Python SDK is the primary one. Concepts include agents, calls, tasks/fields, handlers, campaigns, RAG/LLM, and testing.
- Hosted, low-latency dialog system that connects to our code over a persistent WebSocket. Our backend stays the source of truth.
- Inbound and outbound calling over WebRTC and SIP. Handles turn-taking and barge-in.
- Vendor claims: SOC 2 Type II, HITRUST, PCI DSS, TCPA tooling.

## To verify
- [ ] Does it expose ASR confidence per utterance or per slot? (`speech-robustness.md`)
- [ ] Warm transfer to a human, with context attached? (`escalation.md`)
- [ ] Can recording be turned off per call? (`recording-consent.md`)
- [ ] Data retention and training-use terms (`data-handling.md`)
- [ ] Bring-your-own LLM or RAG, and how our legal corpus plugs in
- [ ] A test harness for simulated calls (feeds `evals/`)

## Verified
<!-- - <fact> — <link> — verified YYYY-MM-DD by <name> -->

## Verified (guava-sdk 0.48.0, read from the installed package and the starter repo, 2026-10-17, Jayesh)
- Use `guava.Agent` + `guava.Call`. `guava.CallController` is marked deprecated in the SDK source.
- Guava's hosted dialog model does STT, TTS, turn-taking, barge-in, and the actual talking. Our code shapes it with `call.set_task(task_id, objective, checklist=[Field|Say|str])`, `call.send_instruction()`, `call.add_info(label, data)`, `call.read_script()` (verbatim, before any LLM turn), `call.hangup(final_instructions)`, `call.transfer(destination, instructions)`.
- A task completes when every required `Field` has a value; `@agent.on_task_complete("task_id")` fires. This makes "intake complete" deterministic.
- Hooks: `on_call_received`, `on_call_start`, `on_caller_speech` (incremental transcripts sharing `utterance_id`), `on_agent_speech` (`interrupted: bool`), `on_question`, `on_action_request` / `on_action(key)`, `on_escalate`, `on_session_end`.
- Auth: `GUAVA_API_KEY`, else a deploy token, else the CLI session from `guava login` (`~/Library/Application Support/guava/config.json` on macOS).
- Testing without a phone: `agent.chat()` (terminal), `agent.listen_webrtc()` (browser link), `agent.call_local()` (mic), `agent.roleplay(prompt)` + `session.evaluate(pass_criteria, fail_criteria)`, `agent.test()` for scripted sessions. Source: `guava/examples/agent_testing.py`.
- Server-side LLM with JSON schema output: `guava.helpers.llm.generate(prompt, json_schema=...)`. Uses the same auth. No OpenAI key needed.
- `IntentRecognizer` in `guava.helpers.openai` needs an OpenAI key; `guava.helpers.llm` has a server-backed variant.
- Not found in the SDK: per-utterance ASR confidence. Confirm critical slots by read-back.
