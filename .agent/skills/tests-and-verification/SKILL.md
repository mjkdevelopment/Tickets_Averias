    ---
    name: tests-and-verification
    description: "Use when modifying behavior. Ensures correct tests, adds missing ones, and provides a verification checklist."
    ---
    # Tests & Verification

## Minimum checks (pick what applies)
- Frontend: `npm run lint` (or scoped lint), `npm run build`
- Backend: `pytest` or `python manage.py test`
- End-to-end smoke path (user flow)

## When to add tests
Add tests if you change:
- Auth/session handling
- Money/odds calculations
- Ticket creation / payout
- Permissions / role gates
- Any bugfix

## Output (required)
- Which commands you ran + results
- Which tests you added/updated and why
- Manual smoke checklist (3–10 steps)
