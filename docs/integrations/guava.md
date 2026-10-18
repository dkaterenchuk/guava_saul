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
