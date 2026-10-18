# Build Plan — Saul Goodman & Associates Voice Agent

See `agent-idea.md` for the idea. This file is the architecture and the build order.

## 1. Architecture

```
Caller (phone / Guava web client)
        │  audio
        ▼
Guava platform ──── STT ────▶  SaulController (guava.CallController)
   ▲                                │
   │ TTS (with barge-in)            ├── Phase state machine
   │                                ├── CaseFile (slot-filling checklist)
   │                                └── Claude calls
   │                                      • extract slots + next question
   │                                      • generate advice (JSON)
   └────────────────────────────────      • answer "why?" / classify interruption
```

Guava owns the audio path: telephony or WebRTC, speech-to-text, text-to-speech, and interruption detection. We write the controller that decides what to say next.

### What we know about the Guava SDK (verify in step 1 of the build order)

- Install: `pip install guava-sdk` (Python 3.10+).
- Base class for an agent: `guava.CallController`. Account-level resources via `guava.Client`.
- Env vars: `GUAVA_API_KEY`, `GUAVA_AGENT_NUMBER`.
- Docs: https://docs.goguava.ai (quickstart at `/getting-started/quickstart`). Starter repo: https://github.com/goguava-ai/guava-starter (see `docs/sdk-reference.md`, 65 examples).
- **Open question:** does the SDK bundle an LLM, or do we call one ourselves? This plan assumes we call Claude directly from the controller. If the SDK has a built-in LLM with tool calling, use that for the intake turns and keep Claude for the one-shot advice generation.

## 2. Call state machine

| Phase | Agent behaviour | Exit condition |
|---|---|---|
| `GREET` | Saul intro, "this is a demo, not legal advice", "tell me what happened" | First caller turn |
| `INTAKE` | Listen. Extract facts into CaseFile. Ask one follow-up per turn for the next empty required slot. | All required slots filled, or caller says "that's everything" |
| `CONFIRM` | Read back a 3–4 sentence summary. "Did I get that right?" | Caller confirms. If not, back to `INTAKE` with the correction. |
| `ADVICE` | Generate advice JSON once. Speak it in chunks: do's → don'ts → options with pros/cons. Pause briefly after each chunk. | All chunks delivered |
| `QA` | Interrupt-driven. Answer "why?", "what if…", re-explain. Offer to resume. | Caller says they're done, or silence timeout |
| `WRAP` | Recap top 3 actions. Repeat disclaimer. Goodbye. | Hang up |

Any phase: if the caller describes an active emergency, say "call 911" and end.

## 3. CaseFile (story-complete detection)

Required slots:

| Slot | What it holds |
|---|---|
| `what_happened` | The incident in the caller's words |
| `when_where` | Date/time and place |
| `parties_involved` | Other people: victim, accuser, cops, store, landlord |
| `police_contact` | `none` / `questioned` / `cited` / `arrested` |
| `charges_or_court_dates` | Anything formal so far, or "none yet" |
| `statements_already_made` | What the caller has said to police, the other party, or online |
| `evidence_witnesses` | Video, texts, receipts, people who saw it |
| `caller_goal` | What outcome they want |

Optional: `prior_record`, `has_lawyer`.

After every caller turn in `INTAKE`, one Claude call returns `{ "slot_updates": {...}, "next_line": "..." }`. The controller merges updates into the CaseFile. `INTAKE` ends when `is_complete()` is true (all required slots non-empty) or the caller signals they're done. The agent asks for at most one missing slot per turn, phrased conversationally, not as a form.

## 4. Advice generation

One Claude call at the `CONFIRM → ADVICE` transition. Input: the CaseFile. Output JSON:

```json
{
  "do":   [ { "action": "...", "why": "..." } ],
  "dont": [ { "action": "...", "why": "..." } ],
  "options": [
    { "name": "...", "pros": ["..."], "cons": ["..."], "saul_take": "..." }
  ],
  "top3": [ "...", "...", "..." ]
}
```

Rules baked into the prompt:
- Universal, non-jurisdictional. No statutes, no promised outcomes.
- "Get a real lawyer" is always one of the options.
- Each `action` is one spoken sentence. The reasoning lives in `why`.
- Max 3 do's, 3 don'ts, 3 options. Voice can't carry more.

The JSON is stored on the session. `advice.py` turns it into an ordered list of short spoken chunks (≈2 sentences each). The `why` fields are what the `QA` phase reads from when the caller interrupts, so the explanation always matches what was just said.

## 5. Interruption handling

- Guava barge-in stops TTS when the caller speaks. The controller records which chunk was interrupted.
- The caller's utterance is classified (keyword rules first, cheap Claude call as fallback):

| Class | Action |
|---|---|
| `why` | Answer from the stored `why` / pros / cons for that chunk. Then "want me to keep going?" |
| `new_fact` | Update CaseFile. Regenerate advice. Resume from the interrupted chunk. |
| `continue` / `skip` | Next chunk. |
| `done` | Go to `WRAP`. |

## 6. Prompts (`saul/prompts.py`)

- `PERSONA` — Saul's voice rules: short sentences, one question at a time, no legalese, confident and a little funny. Humour is never used in the disclaimer or the don'ts.
- `INTAKE_SYSTEM` — given CaseFile JSON and the transcript so far, return slot updates and the next spoken line.
- `CONFIRM_SYSTEM` — given CaseFile, return a 3–4 sentence read-back.
- `ADVICE_SYSTEM` — return the advice JSON in section 4.
- `QA_SYSTEM` — given the advice JSON, the interrupted chunk, and the caller's question, answer in at most 3 sentences.
- `CLASSIFY_SYSTEM` — label an interruption as `why` / `new_fact` / `continue` / `done`.

## 7. Repo layout

```
guava_saul/
  agent-idea.md
  plan.md
  README.md
  pyproject.toml            # guava-sdk, anthropic, python-dotenv
  .env.example              # GUAVA_API_KEY, GUAVA_AGENT_NUMBER, ANTHROPIC_API_KEY
  saul/
    __main__.py             # entrypoint: run SaulController
    controller.py           # guava.CallController subclass, phase loop
    case_file.py            # CaseFile dataclass + is_complete()
    llm.py                  # Claude wrappers: intake_turn, confirm, generate_advice, answer_why, classify
    prompts.py
    advice.py               # advice JSON -> ordered spoken chunks
  tests/
    test_case_file.py       # completeness logic
    test_advice_render.py   # chunking, no empty chunks, length caps
    scenarios/              # scripted caller transcripts for text-mode (no voice) runs
```

## 8. Model choice

- `claude-sonnet-5-5` for every per-turn call (intake, classify, QA). Latency matters on a phone call.
- Same model for the one-shot advice generation. Move to `claude-opus-5-5` only if advice quality is weak in rehearsal.

## 9. Build order (hackathon time budget)

| # | Time | Task | Done when |
|---|---|---|---|
| 1 | 15 min | Clone guava-starter, read `docs/sdk-reference.md`, run one example on a real phone. | We know how to speak, how transcripts arrive, how barge-in surfaces, and whether the SDK bundles an LLM. |
| 2 | 30 min | `case_file.py` + `llm.py` intake turn. | Works in a text REPL with no voice. |
| 3 | 30 min | `controller.py`: `GREET → INTAKE → CONFIRM`. | Works on a real call. |
| 4 | 30 min | `generate_advice` + `advice.py` chunking + `ADVICE` phase. | Advice is spoken in chunks on a real call. |
| 5 | 30 min | `QA` phase with interruptions. | "Why?" mid-advice gets a matching answer and resumes. |
| 6 | 20 min | `WRAP`, disclaimer placement, persona polish. | Full call start to finish. |
| 7 | rest | Rehearse the two demo scenarios. Tighten prompts. Record a backup call. | Demo is reliable. |

## 10. Demo script

**Scenario A — DUI stop.** Caller was pulled over last night, did a breathalyzer, was released, no court date yet. Shows the full intake, then three options (plead / fight / get a lawyer first) with pros and cons.

**Scenario B — Shoplifting accusation.** Store security stopped the caller, no police yet, they were asked to sign a form and refused. Shows "don't go back to the store, don't sign anything, don't post about it", then the caller interrupts with "why can't I just go explain?" and gets the matching answer.

## 11. Risks

| Risk | Mitigation |
|---|---|
| SDK programming model differs from this plan | Step 1 of build order happens before any controller code. |
| Two Claude calls per intake turn add latency | One call returns both slot updates and the next line. |
| Advice too long for voice | Hard cap of ≈2 sentences per chunk. Detail lives in `why` for the QA phase. |
| Caller rambles and never fills slots | After 6 intake turns, agent moves to `CONFIRM` with what it has and marks gaps as "unknown". |
| Persona drifts into actual legal claims | `ADVICE_SYSTEM` forbids statutes and outcome promises. "Get a real lawyer" is always an option. |
