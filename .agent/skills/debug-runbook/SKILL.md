    ---
    name: debug-runbook
    description: "Use when something is broken: console overlay, 4xx/5xx, hydration mismatch, printing issues, flaky tests, etc. Forces systematic debugging."
    ---
    # Debug Runbook

## 1) Reproduce + capture
- Exact error text (copy/paste)
- Request: method + URL + payload + status
- Environment: dev/prod, device/browser, commit hash (if available)

## 2) Classify the layer
- UI rendering / state
- Frontend API client / base URL / trailing slash
- Backend routing (Django URLconf)
- Auth (cookie vs JWT) / CORS / CSRF
- DB / migrations

## 3) Verify contracts (no guessing)
- Confirm the backend route exists (list urls / docs)
- Confirm credentials mode (cookies need `credentials: "include"`)
- Confirm trailing slashes

## 4) Apply smallest fix
- Fix one thing, retest, repeat.

## 5) Output (required)
- Root cause
- Fix summary
- Files changed
- Commands run + results
- Repro steps confirming fixed
