"""Run the Saul agent.

  python -m saul --chat               text chat in the terminal (no audio, uses Guava's test session)
  python -m saul --webrtc             prints a browser link; talk to the agent with your mic
  python -m saul --local              talk through your computer's mic and speakers
  python -m saul --phone [+1...]      listen on your Guava number (defaults to GUAVA_AGENT_NUMBER)
  python -m saul --roleplay dui       automated test: an LLM plays the caller, then the transcript is graded
  python -m saul --roleplay all
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv


def main() -> int:
    load_dotenv()
    from guava import logging_utils

    logging_utils.configure_logging()
    logging.getLogger("saul").setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="Saul Goodman & Associates intake agent (demo)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--chat", action="store_true", help="Text chat in the terminal.")
    group.add_argument("--webrtc", metavar="CODE", nargs="?", const="", help="Browser call. Prints a link.")
    group.add_argument("--local", action="store_true", help="Call using the local mic and speakers.")
    group.add_argument("--phone", metavar="NUMBER", nargs="?", const="", help="Listen on a phone number.")
    group.add_argument("--roleplay", metavar="SCENARIO", help="Run a roleplay scenario, or 'all'.")
    parser.add_argument(
        "--dashboard", metavar="PORT", nargs="?", const=8765, type=int,
        help="Also serve the operator console (live turn-by-turn transcript) on this port. Default 8765.",
    )
    args = parser.parse_args()

    from .agent import agent
    from .llm import _claude_available, model_id

    if args.dashboard:
        from . import dashboard

        url = dashboard.start(port=args.dashboard)
        print(f"\n  Operator console: {url}\n", flush=True)

    logging.getLogger("saul").info(
        "advice LLM: %s", f"claude ({model_id()})" if _claude_available() else "guava server LLM (no ANTHROPIC_API_KEY)"
    )

    if args.chat:
        agent.chat()
    elif args.webrtc is not None:
        agent.listen_webrtc(args.webrtc or None)
    elif args.local:
        agent.call_local()
    elif args.phone is not None:
        number = args.phone or os.environ.get("GUAVA_AGENT_NUMBER", "")
        if not number:
            print("Set GUAVA_AGENT_NUMBER or pass --phone +1...", file=sys.stderr)
            return 2
        agent.listen_phone(number)
    elif args.roleplay:
        return run_roleplay(args.roleplay)
    return 0


def run_roleplay(name: str) -> int:
    from .scenarios import SCENARIOS
    from .agent import agent

    names = list(SCENARIOS) if name == "all" else [name]
    unknown = [n for n in names if n not in SCENARIOS]
    if unknown:
        print(f"Unknown scenario(s): {unknown}. Choose from: {list(SCENARIOS)}", file=sys.stderr)
        return 2

    # Roleplay callers are synthetic, so full case dumps in the log are fine here.
    os.environ.setdefault("SAUL_DEBUG_SYNTHETIC", "1")

    failures = 0
    for n in names:
        sc = SCENARIOS[n]
        print(f"\n===== roleplay: {n} =====")
        try:
            session = agent.roleplay(sc.caller_prompt)
        except Exception as exc:  # Guava's test websocket sometimes drops without a close frame
            failures += 1
            print(f"--- {n}: ERROR (test session dropped: {type(exc).__name__}: {exc}) ---")
            continue
        print("\n--- transcript ---")
        print(session.get_transcript())
        try:
            session.evaluate(pass_criteria=sc.pass_criteria, fail_criteria=sc.fail_criteria)
            print(f"--- {n}: PASS ---")
        except Exception as exc:  # evaluate() raises on failure
            failures += 1
            print(f"--- {n}: FAIL ---\n{exc}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
