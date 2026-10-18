# Business case and feature brainstorm

> **Owner:** track 1. **Context:** this is a **Guava hackathon**, so the business case has to do two jobs: be a credible business *and* show off as much of Guava's voice platform as possible in a coherent story. Every feature below is mapped to the Guava capability it demonstrates. Figures are sourced; anything marked *(assumption)* still needs validating.
>
> **Constraint (2026-10-17): no outbound calling.** Everything below is inbound calls, live supervision, and SMS. SMS may also need registration (see Guava's "Outbound & SMS Compliance" guide), so confirm it at the event.

## 1. What Guava does well (what the demo should show off)

From the official docs index ([docs.goguava.ai/llms.txt][gdocs]) and the Daytona launch ([CMSWire][daytona]):

| Guava capability | SDK / guide | Why it matters for us |
|---|---|---|
| Natural, fast speech | Daytona model. It led its own benchmark on fidelity, speech quality, and response time. | Stressed callers stay on the line |
| Structured intake | `Task`, `Field`, `get_field()`, `on_task_complete()` | Intake turns straight into a ticket |
| Grounded answers | `DocumentQA` (RAG), `on_question()` | "Know your rights" answers come from vetted docs, not improvised |
| Classify the caller's request | Intent helpers, `on_action_request()` | Case type: DUI, theft, assault, tenant |
| Change course mid-call | `set_task()`, `send_instruction()` | Emergency detected → switch tasks; a **live attorney whisper** |
| Multilingual | `set_language_mode()` | A caller switches to Spanish mid-call |
| Hand off to a human | `on_escalate()`, `transfer()`, **warm transfers** | The agent briefs the attorney, then connects the caller |
| SMS | Messaging guide, Messages API | Text the caller a recap of the do's and don'ts |
| Scheduling on the inbound call | `DatetimeFilter` | Book the consult during the call ("tomorrow-ish, morning") |
| Keypad input | `on_caller_dtmf()` | "Press 1 to confirm" for a booking or a date, which is robust when the line is noisy |
| Browser calling | WebRTC widget (one script tag) | Judges can call from the demo page; also a firm-website widget |
| Live transcript stream | `on_caller_speech()`, `on_agent_speech()` | Dashboard shows the call live |
| Data and retention | Conversations API (transcripts, recordings), Delete conversation | The dashboard's data source; deletion for retention compliance |
| Testing | Automated agent testing | Our eval suite runs on Guava's own test tooling |

*Caveat from Guava's own benchmark:* across all systems tested, evaluators preferred humans 93% of the time on **interruption recovery** ([CMSWire][daytona]). Barge-in is hard for everyone, so rehearse that part of the demo; don't improvise it on stage.

## 2. The problem, in numbers

- **Firms don't answer.** In Clio's 2024 mystery-shop study of 1,000 US firms, only **40% answered** a prospective client's call, only **20%** returned missed calls, and **48%** couldn't be reached by phone at all ([Clio][clio]).
- **Clients miss court.** Failure-to-appear rates can reach ~30% depending on jurisdiction, and failing to appear is criminalized in 46 states. In one randomized study, text reminders plus a redesigned summons cut it by **21%** ([J-PAL][jpal]). Many missed appearances come from forgetting or missing information. *(This is the case for SMS reminders, if SMS is allowed.)*
- **People can't get help.** Low-income Americans get no or insufficient help for **92%** of their substantial civil legal problems ([LSC][lsc]).

These come from secret-shopper tests and policy summaries. Use them as directional evidence.

## 3. Options, scored on business strength and how much of Guava they show

| Option | Story | Guava capabilities shown | Business | Verdict |
|---|---|---|---|---|
| A. Inbound front door | Answers the firm's calls at 2am, does intake, creates a ticket | Inbound, Fields, RAG, transfer (~5) | Crowded market (Smith.ai, AI receptionists) | Too narrow for the showcase |
| **B. AI + attorney on the same call: "Saul answers, the attorney steers"** | Inbound intake → live transcript → attorney whisper → warm transfer if urgent → consult booked on the call → SMS recap (+ court-date reminder text) | **Inbound, Fields, RAG, mid-call task switch, live instructions, warm transfer, multilingual, scheduling, DTMF, SMS, WebRTC, Conversations API (~12)** | The firm never misses a call, the attorney only steps in where they add value, and the client leaves with a booked consult | **Recommended** |
| C. Multilingual legal aid hotline | Triage for a legal aid org, in English and Spanish | Inbound, multilingual, RAG, transfer (~5) | Grant-funded, weak revenue | Use as the "impact" slide, not the product |
| ~~D. Outbound reminders~~ | ~~Court reminder calls~~ | n/a | n/a | **Out: no outbound calling.** SMS reminders survive inside B if SMS is allowed. |

**Why B:** one coherent product that pairs AI with a human on the same live call. That's the most interesting thing a voice platform can do, and the thing receptionist products don't do. Every Guava feature has a reason to exist in the story, rather than being bolted on to tick a box.

**Pitch line:**
> *Half of law firms don't pick up. Saul answers every call and helps the caller right then. When it matters, the attorney steers the call live, without ever picking up the phone, or Saul hands it to them with a briefing.*

## 4. Competition and wedge

- Hybrid human + AI receptionists (Smith.ai, Ruby, LEX Reception) at roughly $10/call; AI-only intake tools at about $100–400/month ([Lawmatics][lawmatics], [Perspective][perspective]). These are vendor blog figures.
- **Our wedge:** they *take a message*. With Saul, **the AI and the attorney work the same live call**: the AI handles the routine, and the attorney steers or takes over in one click. That's also what shows off Guava's platform rather than just its speech quality.

## 5. Feature brainstorm, ranked by demo impact per build hour

**P0** = the demo doesn't work without it. **P1** = a big wow if time allows. **Cut** = not for the hackathon.

### Act 1: The 2am call (track 2)
| Pri | Feature | Guava capability | Business reason |
|---|---|---|---|
| P0 | Disclaimer as an opening script; Saul persona | `read_script()`, `set_persona()` | Required, and it sets the tone |
| P0 | Story intake into structured fields | `Task`, `Field`, `on_task_complete()` | Becomes the ticket |
| P0 | Immediate do's and don'ts ("don't sign anything, don't post about it") | `DocumentQA` over a vetted "know your rights" doc | Caller helped *now*; grounded, not improvised |
| P0 | Read-back confirmation | Task design | Trust plus ticket accuracy |
| P0 | Emergency → switch to the safety task, give 911 | `set_task()` | Safety; shows a mid-call pivot |
| P1 | **Mid-call language switch to Spanish** | `set_language_mode()` | A big live-demo moment; access-to-justice angle |
| P1 | Case-type classification | Intent helpers | Routing and ticket field |

### Act 2: The attorney steps in (tracks 2 and 3)
| Pri | Feature | Guava capability | Business reason |
|---|---|---|---|
| P0 | Live transcript in the dashboard | `on_caller_speech()` / `on_agent_speech()` | The legal team can see the call as it happens |
| P1 | **Attorney "whisper":** types "ask whether they consented to the search" → Saul asks it naturally | `send_instruction()` | **The signature demo moment.** Human-in-the-loop AI with no handoff. |
| P1 | **Warm transfer:** urgent case (arrested now, court in 2 days) → Saul briefs the on-call attorney, then connects the caller | Warm transfers, `transfer()` | Shows when the AI should step aside |
| P1 | Caller says "let me talk to a person" | `on_escalate()` | Required behavior |

### Act 3: Follow-through (tracks 2 and 3)
| Pri | Feature | Guava capability | Business reason |
|---|---|---|---|
| P0 | Ticket in the review queue, urgency first; approve / edit / escalate | Conversations API (transcript + recording) | The legal team's workflow |
| P0 | **Book the consult on the call:** "How's tomorrow morning?" → a slot, confirmed by voice or by pressing 1 | `DatetimeFilter`, `on_caller_dtmf()` | The conversion event; mock the calendar |
| P1 | SMS recap to the caller: top 3 do's and don'ts, the booked slot, the firm's number | Messaging / Messages API | The caller has it in writing *(if SMS is allowed)* |
| P1 | Court-date reminder **text**, scheduled from the ticket's `deadlines` field | Messages API | Evidence-backed value (J-PAL) *(if SMS is allowed)* |
| P1 | Overnight dashboard summary: "while you slept: N calls, M qualified, K urgent" | Conversations API | Business story on one screen |

### Platform credibility (track 2)
| Pri | Feature | Guava capability | Business reason |
|---|---|---|---|
| P0 | Judges call from the browser | WebRTC widget | Nobody needs a phone number to try it |
| P1 | Eval scenarios run as automated Guava tests | Automated agent testing | Shows engineering rigor; ties to `evals/` |
| P1 | "Delete my data" honored | Delete conversation API | Compliance with privacy; a one-line pitch point |
| Cut | CRM sync, multiple states, payments, full role management | n/a | Mention as roadmap only |

**If time runs short, build in this order:** Act 1 P0 → consult booking → ticket queue → live transcript → whisper → warm transfer → SMS → Spanish.

## 6. Demo storyline (≈3 minutes)
1. **Hook (15s):** "Half of law firms don't pick up when a new client calls." *(Clio)*
2. **Act 1 (60s):** a judge calls from the browser as a DUI caller. Saul gives the disclaimer, gets the story, gives immediate don'ts from the knowledge base, and reads the story back. One **rehearsed** interruption: "wait, why?" *(Optional: the caller switches to Spanish.)*
3. **Act 2 (45s):** split screen with the dashboard showing the live transcript. The attorney types a whisper, and Saul asks the question naturally. The caller mentions a court date in 2 days → warm transfer: Saul briefs the attorney first.
4. **Act 3 (45s):** *(alternative ending if the transfer isn't built: Saul books the consult and the caller presses 1 to confirm.)* The caller's phone gets an SMS recap. The dashboard shows the ticket at the top of the queue with one low-confidence field, and the attorney edits and approves it.
5. **Close (15s):** the pitch line, the Guava features used (one slide with ~12 bullets), and the roadmap (outbound reminders and callbacks come next).

## 7. Pricing hypothesis (one line in the pitch)
Per-firm SaaS in the AI-intake range ($100–400/month) plus usage, or per qualified lead. It must cover Guava per-minute costs plus LLM costs (get pricing at the event).

## 8. Open questions for the team
- [ ] Hackathon judging criteria: check the event page or briefing. If "use of Guava" is scored, option B's breadth matters even more.
- [ ] Do live warm transfer and the whisper work in the time available? Spike `send_instruction()` and warm transfer **first**, since they're the highest-value and highest-risk features.
- [ ] Is SMS allowed at the event, or does it need registration (Guava's "Outbound & SMS Compliance" guide)? If not, show the recap on screen instead.
- [ ] Interruption rehearsal: script the exact line and moment, run it 10+ times on the demo laptop/mic/browser, and keep a recorded backup.
- [ ] Who plays the attorney in the live demo?

[gdocs]: https://docs.goguava.ai/llms.txt
[daytona]: https://www.cmswire.com/the-wire/guava-launches-daytona-a-state-of-the-art-voice-model/
[clio]: https://www.clio.com/about/press/clios-legal-trends-report-reveals-law-firms-struggle-to-respond-to-client-inquiries/
[jpal]: https://www.povertyactionlab.org/print/pdf/node/8134631
[lsc]: https://lsc.gov/press-release/low-income-americans-face-immense-justice-gap-according-new-legal-services-corporation-report
[lawmatics]: https://www.lawmatics.com/blog/best-ai-receptionists-for-law-firms
[perspective]: https://getperspective.ai/blog/best-legal-answering-services-2026-8-options-compared-vs-ai-intake
