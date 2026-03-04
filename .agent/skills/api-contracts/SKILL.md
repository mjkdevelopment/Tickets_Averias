    ---
    name: api-contracts
    description: "Use when touching endpoints or API calls. Keeps a single source of truth for base paths, errors, and auth headers/cookies."
    ---
    # API Contracts

## Rules
- Never invent endpoints. Verify backend routes.
- Keep ONE base URL constant (e.g., `/api`).
- Be consistent with trailing slashes if backend expects them.
- If backend returns HTML 404/debug pages, treat it as wrong route (or wrong host).

## Auth
- Session cookies: `credentials: "include"`
- JWT: attach `Authorization: Bearer <token>` consistently

## Error handling
- Prefer JSON errors. If response isn't JSON, include status + short snippet for debugging.

## Output (required)
- Endpoint(s) touched
- Expected status codes
- Example request/response payloads
