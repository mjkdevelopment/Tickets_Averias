    ---
    name: change-protocol
    description: "Always use for feature/refactor work. Enforces minimal diffs, plan→execute→verify, evidence, and safe handling of secrets."
    ---
    # Change Protocol (Always)

## Before you start
1) Restate the goal in 1–2 lines.
2) List the exact files you expect to touch.
3) Define “Done” (what the user will see / which tests will pass).

## While editing
- Keep diffs minimal. No drive‑by refactors.
- Follow existing patterns in the repo.
- Never output secrets (.env, keys, tokens). Redact if needed.

## After editing (required)
Provide:
- Files changed + why
- Commands run (lint/test/build) and results
- How to verify manually (click-path / curl)
- Risks / rollback note
