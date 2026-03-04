# Always-on rules (Generic)

- Never expose secrets (.env, tokens, keys). Redact if needed.
- Make minimal, scoped diffs. No refactors unless requested.
- Before coding: state the plan in 3–6 bullets.
- After coding: list files changed + why + exact commands run + how to verify.
- Prefer existing patterns in the repo (naming, folders, APIs).
- If an API call fails: verify backend routes; don’t invent endpoints.
- Mobile UI must respect iOS safe-area + keyboard + bottom nav.
- Add/adjust tests when behavior changes.
