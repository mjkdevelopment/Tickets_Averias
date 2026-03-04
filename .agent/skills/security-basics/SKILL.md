    ---
    name: security-basics
    description: "Use for any auth, payout, ticketing, admin features, or data exposure. Enforces idempotency, auditability, and secret handling."
    ---
    # Security Basics

## Never
- Expose secrets: .env, API keys, device tokens, private keys
- Allow unauthenticated payout / settlement

## Always
- Idempotency for money actions (pay, settle, create ticket)
- Audit log entry for critical actions
- Rate limit / lockout on sensitive endpoints (login, redeem)
- Validate inputs (UUIDs, amounts, odds)

## Output (required)
- Threats considered (2–5 bullets)
- Mitigations applied
- Tests/verification steps
