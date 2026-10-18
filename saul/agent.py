"""The Saul Goodman & Associates intake agent.

Phases are Guava tasks, driven by deterministic code (never by the LLM):

  GREET (read_script) -> intake -> confirm -> advice -> wrap
                              \\-> safety (any time a danger signal is heard; S2)
                              \\-> handoff (any time the caller asks for a person; C4)

Guava's hosted dialog model does the talking, turn-taking, and barge-in. Our code decides which
task is active, fills the case file, generates the advice once, and answers "why?" questions.
"""
from __future__ import annotations

import json
import logging
import os
import threading

import guava
from guava.events import AgentSpeechEvent, BotSessionEnded, CallerSpeechEvent, EscalateEvent

from . import prompts, safety
from .advice import Advice, advice_chunks, advice_notes
from .case_file import CaseFile, intake_fields
from .dashboard import bus, mask_number
from .llm import answer_question, generate_advice

logger = logging.getLogger("saul.agent")

agent = guava.Agent(
    name="Saul",
    organization=prompts.FIRM,
    purpose=prompts.AGENT_PURPOSE,
    voice="jack",
)


# ---------------------------------------------------------------------------
# Per-call state helpers (stored on the Call so handlers stay stateless)
# ---------------------------------------------------------------------------

def _phase(call: guava.Call) -> str:
    return call.get_variable("phase", "greet")


def _set_phase(call: guava.Call, phase: str) -> None:
    logger.info("phase -> %s", phase)
    call.set_variable("phase", phase)
    bus.emit(call.id, "phase", phase=phase)


def _call_label(call: guava.Call) -> str:
    info = call.call_info
    kind = getattr(info, "call_type", "call")
    if kind == "pstn":
        return f"phone {mask_number(getattr(info, 'from_number', None))}"
    if kind == "webrtc":
        return "browser"
    return kind


def _case(call: guava.Call) -> CaseFile | None:
    data = call.get_variable("case")
    return CaseFile.from_dict(data) if data else None


def _advice(call: guava.Call) -> Advice | None:
    data = call.get_variable("advice")
    return Advice.model_validate(data) if data else None


# ---------------------------------------------------------------------------
# Call lifecycle
# ---------------------------------------------------------------------------

@agent.on_call_received
def on_call_received(call_info: guava.CallInfo) -> guava.IncomingCallAction:
    return guava.AcceptCall()


@agent.on_call_start
def on_call_start(call: guava.Call) -> None:
    bus.emit(call.id, "call_start", label=_call_label(call))
    # S1: AI + recording disclosure and the demo disclaimer, verbatim, before any LLM turn.
    call.read_script(prompts.DISCLOSURE_SCRIPT)
    _start_intake(call)


def _start_intake(call: guava.Call, resuming: bool = False) -> None:
    _set_phase(call, "intake")
    objective = prompts.INTAKE_OBJECTIVE
    if resuming:
        objective += " You already have some of the caller's story; do not re-ask anything they've told you."
    call.set_task("intake", objective=objective, checklist=intake_fields())


@agent.on_task_complete("intake")
def on_intake_done(call: guava.Call) -> None:
    case = CaseFile.from_call(call)
    call.set_variable("case", case.to_dict())
    logger.info("intake complete; empty fields: %s", case.missing() or "none")
    _debug_dump("case", case.to_dict())
    bus.emit(call.id, "case", case=case.to_dict())
    _start_confirm(call, case)


def _start_confirm(call: guava.Call, case: CaseFile) -> None:
    _set_phase(call, "confirm")
    checklist: list = [guava.Say(case.summary_text())]
    if case.has_deadline():
        # S6: deadlines surface early and get confirmed.
        checklist.append(
            f"Confirm the date or deadline you heard: '{case.charges_or_court_dates}'. "
            "Say it back and ask if that's right."
        )
    checklist += [
        guava.Field(
            key="summary_correct",
            question="Did I get that right?",
            field_type="multiple_choice",
            choices=["yes", "no"],
        ),
        guava.Field(
            key="correction",
            description="Only if they said no: what needs fixing, in their words. Skip if they said yes.",
            required=False,
        ),
    ]
    call.set_task("confirm", objective=prompts.CONFIRM_OBJECTIVE, checklist=checklist)


@agent.on_task_complete("confirm")
def on_confirm_done(call: guava.Call) -> None:
    case = _case(call) or CaseFile.from_call(call)
    correct = (call.get_field("summary_correct") or "no").lower()
    correction = (call.get_field("correction") or "").strip()
    if correct != "yes":
        attempts = int(call.get_variable("confirm_attempts", 0)) + 1
        call.set_variable("confirm_attempts", attempts)
        if correction:
            case.corrections.append(correction)
            call.set_variable("case", case.to_dict())
            bus.emit(call.id, "case", case=case.to_dict())
        if attempts >= 2:
            # Still unsure of key facts after a correction: that's a lawyer conversation, not guidance.
            call.send_instruction("Tell the caller you want a person to go over the details with them rather than guess.")
            _start_handoff(call)
            return
        _start_confirm(call, case)
        return
    # Advice generation can take a few seconds. Don't block the event loop. Guava fills the gap itself.
    threading.Thread(target=_deliver_advice, args=(call, case), daemon=True).start()


def _deliver_advice(call: guava.Call, case: CaseFile) -> None:
    advice, provider = generate_advice(case)
    logger.info("advice generated by %s", provider)
    _debug_dump("advice", advice.model_dump())
    if _phase(call) in {"safety", "handoff", "wrap"}:
        # A safety signal or handoff started while we were generating. Don't clobber it.
        logger.info("advice ready but phase is %s; not delivering", _phase(call))
        return
    call.set_variable("advice", advice.model_dump())
    call.set_variable("advice_provider", provider)
    call.add_info("advice_notes", advice_notes(advice))
    bus.emit(call.id, "advice", advice=advice.model_dump(), provider=provider)

    _set_phase(call, "advice")
    checklist: list = []
    for chunk in advice_chunks(advice):
        checklist.append(guava.Say(chunk))
        checklist.append("Pause. Check in with one short question, and answer any question they have before continuing.")
    checklist.append(
        guava.Field(
            key="advice_done",
            question="That's the whole picture. Anything you want me to go back over?",
            description="Whether the caller has any remaining questions. Record 'done' once they have none.",
            field_type="multiple_choice",
            choices=["done", "has_questions"],
        )
    )
    call.set_task(
        "advice",
        objective=prompts.ADVICE_OBJECTIVE,
        checklist=checklist,
        completion_criteria="Every chunk has been said and the caller has no more questions.",
    )


@agent.on_task_complete("advice")
def on_advice_done(call: guava.Call) -> None:
    if (call.get_field("advice_done") or "done") == "has_questions":
        call.send_instruction("Answer their remaining questions from advice_notes, briefly, then ask if that covers it.")
    _wrap(call)


def _wrap(call: guava.Call) -> None:
    _set_phase(call, "wrap")
    advice = _advice(call)
    top3 = "; ".join(advice.top3) if advice else "write it all down, save your evidence, talk to a lawyer"
    call.hangup(final_instructions=f"The top three actions are: {top3}. {prompts.WRAP_INSTRUCTIONS}")


# ---------------------------------------------------------------------------
# Safety layer: runs on every caller utterance, before anything else (S2)
# ---------------------------------------------------------------------------

@agent.on_caller_speech
def on_caller_speech(call: guava.Call, event: CallerSpeechEvent) -> None:
    utterance = event.utterance or ""
    # Live transcript for the operator console (in memory only). Same utterance_id = same turn, refined.
    bus.emit(call.id, "caller", id=f"c-{event.utterance_id}" if event.utterance_id else None, text=utterance)
    signal = safety.scan(utterance)
    if signal is None:
        # C4: "get me a person" is handled in code, not left to the hosted model's judgment.
        if safety.wants_human(utterance) and _phase(call) not in {"handoff", "safety", "wrap"}:
            logger.info("caller asked for a human")
            bus.emit(call.id, "note", text="caller asked for a person; starting callback flow")
            _start_handoff(call)
        return
    if _phase(call) == "safety":
        # Already in the safety task (transcripts arrive incrementally). Re-trigger later if it comes up again.
        return
    handled = set(call.get_variable("safety_handled", []))
    handled.add(signal.category)
    call.set_variable("safety_handled", sorted(handled))
    call.set_variable("resume_phase", _phase(call))
    logger.warning("safety signal: %s", signal.category)
    bus.emit(call.id, "safety", category=signal.category)
    _start_safety(call, signal)


def _start_safety(call: guava.Call, signal: safety.SafetySignal) -> None:
    _set_phase(call, "safety")
    # The hosted model may already be mid-reply. Both commands go out: the instruction to stop now,
    # and the task switch that replaces the checklist.
    call.send_instruction(
        "STOP. Do not ask any more intake questions. The caller just said something about their safety. "
        "Say the safety checklist item now, word for word."
    )
    call.set_task(
        "safety",
        objective=safety.safety_followup_objective(signal),
        checklist=[
            guava.Say(safety.safety_script(signal)),
            guava.Field(
                key="safe_now",
                description="Whether the caller says they are safe right now.",
                field_type="multiple_choice",
                choices=["safe", "not_safe", "unclear"],
            ),
            guava.Field(
                key="continue_intake",
                question="Do you want to keep going with the legal side, or stop here?",
                field_type="multiple_choice",
                choices=["continue", "stop"],
            ),
        ],
    )


@agent.on_task_complete("safety")
def on_safety_done(call: guava.Call) -> None:
    safe = call.get_field("safe_now") or "unclear"
    cont = call.get_field("continue_intake") or "stop"
    if safe != "safe" or cont == "stop":
        call.hangup(
            final_instructions=(
                "Repeat the emergency number 911 and the hotline you gave. Tell them they can call back any time. "
                "Say goodbye gently and hang up."
            )
        )
        return
    if "active_arrest" in call.get_variable("safety_handled", []):
        # escalation.md: rights information plus a defense referral. No case analysis.
        _start_handoff(call)
        return
    resume = call.get_variable("resume_phase", "intake")
    if resume == "intake":
        _start_intake(call, resuming=True)
    elif resume == "confirm":
        case = _case(call) or CaseFile.from_call(call)
        _start_confirm(call, case)
    elif resume == "advice":
        case = _case(call) or CaseFile.from_call(call)
        threading.Thread(target=_deliver_advice, args=(call, case), daemon=True).start()
    else:
        _wrap(call)


# ---------------------------------------------------------------------------
# Questions, interruptions, and "get me a person"
# ---------------------------------------------------------------------------

@agent.on_question
def on_question(call: guava.Call, question: str) -> str:
    """Fires when the hosted model can't answer from context. Runs in a background thread."""
    phase = _phase(call)
    if phase == "safety":
        return "I don't want to guess on that. The numbers I gave you are free and open any time. Are you safe right now?"
    if phase == "handoff":
        return "An attorney will go over that with you on the callback. What's the best number to reach you?"
    case = _case(call)
    advice = _advice(call)
    if case is None or advice is None:
        return prompts.HOLD_THAT_THOUGHT
    answer = answer_question(case, advice, question)
    bus.emit(call.id, "note", text=f"question routed to LLM: {question[:80]}")
    return answer


@agent.on_agent_speech
def on_agent_speech(call: guava.Call, event: AgentSpeechEvent) -> None:
    bus.emit(call.id, "agent", text=event.utterance or "", interrupted=bool(event.interrupted))
    if event.interrupted:
        call.set_variable("last_interrupted", event.utterance)
        logger.info("caller interrupted the agent")
    _emit_partial_case(call)


def _emit_partial_case(call: guava.Call) -> None:
    """Push the fields collected so far to the console, so they tick off live during intake."""
    if _phase(call) != "intake":
        return
    partial = CaseFile.from_call(call).to_dict()
    filled = {k: v for k, v in partial.items() if v and k != "corrections"}
    if filled and filled != call.get_variable("partial_case_sent"):
        call.set_variable("partial_case_sent", filled)
        bus.emit(call.id, "case", case=partial)


@agent.on_action_request
def on_action_request(call: guava.Call, intent_summary: str):
    if safety.wants_human(intent_summary):
        return guava.SuggestedAction(key="handoff")
    if safety.is_done(intent_summary) and _phase(call) == "advice":
        return guava.SuggestedAction(key="finish")
    return None


@agent.on_action("handoff")
def handoff(call: guava.Call) -> None:
    _start_handoff(call)


@agent.on_action("finish")
def finish(call: guava.Call) -> None:
    _wrap(call)


@agent.on_escalate
def on_escalate(call: guava.Call, event: EscalateEvent) -> None:
    _start_handoff(call)


def _start_handoff(call: guava.Call) -> None:
    # C4: the caller can always reach a human. No live attorney line in the demo, so collect a callback.
    _set_phase(call, "handoff")
    call.set_task(
        "handoff",
        objective=prompts.HANDOFF_OBJECTIVE,
        checklist=[
            guava.Field(key="callback_number", description="Best phone number for an attorney to call back. Read it back to confirm.", sensitive=True),
            guava.Field(key="callback_time", description="Best time of day for the callback.", required=False),
        ],
    )


@agent.on_task_complete("handoff")
def on_handoff_done(call: guava.Call) -> None:
    call.hangup(
        final_instructions=(
            "Confirm an attorney will call them back at the number given. Remind them this was a demo and not legal advice. "
            "Say goodbye and hang up."
        )
    )


@agent.on_session_end
def on_session_end(call: guava.Call, event: BotSessionEnded) -> None:
    # Logs never carry caller text (docs/compliance/data-handling.md). Full dumps only for synthetic runs.
    case = _case(call)
    advice = _advice(call)
    logger.info(
        "session ended: phase=%s reason=%s advice_provider=%s safety=%s",
        _phase(call), event.termination_reason, call.get_variable("advice_provider"), call.get_variable("safety_handled", []),
    )
    bus.emit(call.id, "call_end", reason=str(event.termination_reason))
    _debug_dump("session", {"case": case.to_dict() if case else None, "top3": advice.top3 if advice else None})


def _debug_dump(label: str, data: dict) -> None:
    """Print caller-derived data only when SAUL_DEBUG_SYNTHETIC=1 (set automatically for roleplay runs)."""
    if os.environ.get("SAUL_DEBUG_SYNTHETIC") == "1":
        logger.info("[synthetic %s]\n%s", label, json.dumps(data, indent=2))
