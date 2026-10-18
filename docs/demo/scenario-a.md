# Demo focus: Scenario A, "The 2am DUI call"

> **This is the hackathon target.** Build only what this recording needs. If a feature isn't listed here, it's out of scope until the recording is done. Concept: `docs/business/business-case.md` ("Saul answers, the attorney steers").
>
> - **Build plan (base architecture):** `plan.md`. This scenario **extends** it; see "Changes to plan.md" below.
> - **Ground truth for testing:** `evals/scenarios/demo-dui-2am.md`
> - **Knowledge base for Saul's don'ts:** `docs/demo/knowledge-base.md`
> - **Constraints:** inbound only (no outbound calling). Fictional firm, fictional caller. No real caller data.

## Deliverable
A screen recording of about 2.5 minutes. Left side: the caller (browser call through the WebRTC widget, plus a phone mirror for the SMS). Right side: the firm's dashboard. Each time a Guava feature fires, a caption names it.

## Cast
- **Saul:** the agent.
- **Marcus:** the caller (a teammate). Follows the beats loosely, not word for word.
- **Kim:** the attorney at the dashboard (a teammate).

## Beat sheet
| # | Time | Beat | Must happen | Guava capability |
|---|---|---|---|---|
| 1 | 0:00 | Hook | Title card: "60% of law firms don't answer a new client's call" (Clio 2024), then a clock at 1:47 AM | n/a |
| 2 | 0:08 | Pickup | Disclaimer: AI, not a lawyer, call recorded, then "What happened?" | `read_script()`, `set_persona()` |
| 3 | 0:15 | Story | Marcus rambles: DUI arrest tonight, released, "paper says court Thursday" | Turn-taking, Daytona speech |
| 4 | 0:30 | Urgency first | Saul flags that Thursday is 2 days away *before* asking anything else, then gives the first don'ts | `DocumentQA` + deadline detection |
| 5 | 0:45 | Interruption | Marcus cuts in: "Why can't I just call him and explain?" Saul stops, answers in ≤2 sentences, and resumes | Barge-in |
| 6 | 1:00 | Live dashboard | Transcript streams in; ticket fields fill in live; `breath_test` shows **low confidence** | `on_caller_speech()`, `on_agent_speech()`, `Field` |
| 7 | 1:10 | **Whisper** | Kim types "Ask if they read him his rights before questioning", and Saul asks it naturally in its next turn | `send_instruction()` |
| 8 | 1:30 | Read-back | 3-sentence summary, "Did I get that right?" Marcus corrects one detail, and Saul updates it | Task / Field flow |
| 9 | 1:45 | **Warm transfer** | Saul says it's connecting him to an attorney, the briefing to Kim is audible, then Kim takes the call | Warm transfer |
| 10 | 2:05 | SMS recap | Marcus's phone gets the top 3 don'ts, "Court: Thu 9am", and the firm's number | Messages API |
| 11 | 2:15 | Ticket | Queue shows this ticket at the top, with flags (court ≤ 2 days, transferred, 1 low-confidence field). Kim edits the field and approves; audit entry visible | Conversations API |
| 12 | 2:30 | Close | Pitch line plus a slide listing the Guava capabilities used | n/a |

## Changes to `plan.md`
`plan.md`'s phases (`GREET → INTAKE → CONFIRM → ADVICE → QA → WRAP`) and its `CaseFile` stay the base. This scenario adds the following:

| Change | Where in `plan.md` | Why |
|---|---|---|
| **Early urgency + first don'ts during `INTAKE`**, triggered by a court date or another danger signal, before intake is complete | §2 state machine | Beat 4: the caller is helped *now*, not only after a full intake |
| **Extra `CaseFile` slots for DUI** (optional): `breath_test`, `vehicle_search`, `rights_read` | §3 CaseFile | Needed for the whisper (beat 7) and the low-confidence field (beat 6) |
| **Per-slot confidence** (`high` / `low`) | §3 CaseFile | Beat 6 and beat 11 |
| **Whisper:** dashboard → `send_instruction()`, usable in any phase | New | Beat 7 |
| **Warm transfer** after `CONFIRM` when `charges_or_court_dates` is within 2 days | Replaces `ADVICE`/`QA` for this call | Beat 9: urgent cases go to a human |
| **Ticket + live events to the dashboard** | New | Beats 6 and 11 |
| **SMS recap at `WRAP`** | §2 `WRAP` | Beat 10 |

The slot names in this doc and in the ground truth are `plan.md`'s. If `plan.md` renames a slot, update both.

## Features to build

**P0** = the recording doesn't work without it. **P1** = this recording needs it, but there's a fallback. Spike the **risky** ones first.

### Track 2: Agent and backend
| Pri | Feature | Done when | Risk | Fallback |
|---|---|---|---|---|
| P0 | Persona + disclaimer script | Beat 2 plays the same way every time | Low | n/a |
| P0 | Intake fills `plan.md`'s `CaseFile` slots plus the DUI extras (`breath_test`, `vehicle_search`, `rights_read`) and `has_lawyer` | All slots filled from a natural, rambling story; nothing invented (S9) | Medium | n/a |
| P0 | Deadline detection → urgency line before any other question | Beat 4: "court Thursday" triggers the urgency line in the next turn | Medium | n/a |
| P0 | `DocumentQA` over `knowledge-base.md` | The don'ts come from the knowledge base, not improvised; "why?" answers match it | Low | n/a |
| P0 | Barge-in recovery | Beat 5 works in 4 of 5 takes | **High** | Record a take with no interruption |
| P0 | Read-back with correction | A correction updates the field | Medium | n/a |
| P0 | Ticket generation at call end, with per-field confidence | Ticket matches the ground truth; `breath_test` comes out `low` | Medium | n/a |
| P1 | **Whisper**: dashboard → `send_instruction()` | Saul asks Kim's question within 1 turn, phrased naturally | **High, spike first** | Leave beat 7 out entirely (don't fake it) |
| P1 | **Warm transfer** with a spoken briefing | Kim hears the briefing, then gets connected | **High, spike first** | Saul books a consult instead ("tomorrow at 10?", press 1): `DatetimeFilter` + `on_caller_dtmf()` |
| P1 | SMS recap | Text arrives within 30s of the call ending | Medium (registration?) | Show "recap sent" on the dashboard |

### Track 3: Dashboard
| Pri | Feature | Done when | Fallback |
|---|---|---|---|
| P0 | Live transcript view | Utterances show up within ~1s | n/a |
| P0 | Live ticket fields with confidence badges | Fields fill in during the call; low confidence is visually obvious | Fill at call end |
| P0 | Queue sorted by urgency, then confidence | The demo ticket lands on top, with flags visible | n/a |
| P0 | Ticket detail: transcript + recording next to the fields; edit / approve | Kim can fix `breath_test` and approve in under 15s on screen | n/a |
| P1 | Whisper input box | Typing and sending reaches the agent (pairs with track 2) | Leave beat 7 out |
| P1 | Audit trail entry | Shows "Kim edited breath_test, approved" with a timestamp | n/a |
| Cut | Auth / roles, monitoring charts, history | n/a | One hard-coded login is enough |

### Track 1: Product
| Feature | Done when |
|---|---|
| Knowledge base content | `knowledge-base.md` is complete and every don't has a one-line "why" |
| Ground-truth scenario | `evals/scenarios/demo-dui-2am.md` is final; the ticket is scored against it |
| Hook + closing slides, captions | The stat is sourced; the capability list matches what actually got built |
| Recording | 5+ takes, best one picked; agent audio unedited |

## Build order
1. Spike the **whisper** and **warm transfer** (go/no-go by an agreed time).
2. Intake + knowledge base + deadline detection (beats 2–4).
3. Ticket generation + dashboard queue and detail (beats 6 and 11).
4. Read-back and barge-in tuning (beats 5 and 8).
5. Whisper, transfer, SMS, or their fallbacks (beats 7, 9, 10).
6. Rehearse, record, and edit.

## Recording rules
- **No faked features.** Agent audio is unedited, and cuts happen only between beats. If something isn't built, use its fallback or leave the beat out.
- Record in OBS: screen + system audio + mic. Mirror the phone for the SMS.
- Captions name the real SDK call or feature used.
- Rehearse the interruption (beat 5) on the actual recording setup, and keep a take that has no interruption.
