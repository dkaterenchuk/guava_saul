---
name: write-spec
description: Draft a feature spec in docs/specs/ for guava_saul. Use when someone says "Spec:", asks to write a PRD/spec, or starts non-trivial feature work without one.
---

1. Ask up to 3 clarifying questions if the problem, the caller affected, or the scope is unclear. Don't guess.
2. Read `docs/product/vision.md`, `docs/product/principles.md`, and any relevant `docs/decisions/`.
3. Pick the next number in `docs/specs/`, copy `docs/specs/_TEMPLATE.md` to `NNN-slug.md`, and fill it in.
   - Done criteria must be checkable. Include the eval scenarios to add, by name.
   - List every principle ID the feature touches.
4. Create `docs/worklog/NNN-slug.md` from its template.
5. If the spec conflicts with a principle or ADR, flag it at the top. Don't silently work around it.
