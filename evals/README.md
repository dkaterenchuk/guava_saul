# Evals

Evals are the definition of done for anything caller-facing. Lint and tests aren't enough.

- `scenarios/`: synthetic callers, one file each (copy `_TEMPLATE.md`). Each lists the principle IDs it covers.
- `rubric.md`: how a call transcript is scored.

## Rules
- **Every principle in `docs/product/principles.md` has at least one scenario.**
- **Safety rules (S*) are pass/fail.** One miss blocks the change.
- **Synthetic only.** Scenarios are invented. Never paste real calls, even with details changed.
- **Add scenarios when a bug is found.** Write the scenario that would have caught it, then fix the bug.

Runner: TBD. It depends on Guava's test tooling (see `docs/integrations/guava.md`).
