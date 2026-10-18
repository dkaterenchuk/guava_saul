---
name: add-scenario
description: Add a synthetic eval scenario. Use when someone says "Scenario:", reports an agent bug, or a principle has no coverage.
---

1. Copy `evals/scenarios/_TEMPLATE.md` to `evals/scenarios/<area>-<slug>.md`.
2. Invent the caller. Never base one on a real call, even with details changed.
3. Fill `covers` with principle IDs from `docs/product/principles.md`.
4. Make the pressure points realistic and adversarial. That's where agents fail.
5. Write "Must" and "Must not" as checks a grader could apply to a transcript without judgment calls.
6. If this comes from a bug, write it so the current behavior would fail.
