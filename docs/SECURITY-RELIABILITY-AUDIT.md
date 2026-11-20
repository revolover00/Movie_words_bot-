# Security and reliability review

This targeted source review covers delivery, preparation storage, database
connections, webhook/dashboard controls and production npm dependencies. It is
not a penetration test, compliance certification or guarantee of no remaining bugs.

## Confirmed findings addressed

| Priority | Finding | Change |
| --- | --- | --- |
| High | Node database connections explicitly disabled TLS certificate verification. | Shared verified-TLS configuration removes URL SSL overrides, verifies CA/hostname and sets connection/statement timeouts. Validated with the actual handler against the configured database before rollout. |
| High | Python connection contexts committed/rolled back but did not guarantee connection closure. | Short-lived `db.session()` commits/rolls back and closes, while the separate advisory-lock connection retains its session lifetime. |
| Medium | A failed legacy phrase summary could abort later groups after a successful send. | Summary writes are best effort; the durable per-recipient receipt remains authoritative. |
| Medium | A rejected Telegram file ID was reused for later recipients, and the first recipient's schedule was advanced despite definite rejection. | Invalidate the cache, preserve the refused slot for bounded retry, and skip remaining recipients of that cohort instead of sending the known-invalid reference. No replay of ambiguous sends was added. |
| Medium | Eligibility compared settings and overdue status, but not the snapshot's exact slot. | Match the captured due timestamp when present, including the lookahead path. |
| Medium | A growing file could be read unbounded before a post-read size check. | Read at most the configured media limit plus one byte, then reject oversize content. |
| Medium | Reloading a saved lesson could select a different matching movie while retaining the original caption/source. | Refuse a reloaded clip whose identity differs from the saved lesson; no silent source substitution. |
| Low | Local Serverless credentials and environment variants were not explicitly ignored. | Ignore `.tgcloud/` and `.env.*`, preserving `.env.example`. |

## Validation

- Regression tests cover connection closure on success/failure, exact-slot
  preflight, invalid cached IDs and continuation after legacy-summary failure.
- SQL integration tests and the disposable-schema lifecycle exercise the actual
  scheduling/storage paths without sending to real subscribers.
- The authenticated browser workflow checks the real database handler, subscriber
  search, navigation, mobile overflow and unauthenticated access rejection.
- `npm audit --omit=dev` reported zero known production dependency vulnerabilities
  at review time. This does not cover Python dependencies, unknown vulnerabilities
  or development-only dependencies.

## Remaining operational considerations

- PostgreSQL credentials in a connection URL must remain secret. Python/libpq TLS
  policy still follows the deployment DSN; this review does not certify its CA
  verification settings.
- Telegram has no atomic transaction with the database. Ambiguous sends remain
  uncertain and are not automatically replayed; perfect exactly-once delivery is
  not promised.
- Provider quotas and missing verified content can still delay delivery. No audio
  verification, language matching or CEFR setting was bypassed.
- Database migrations still run during webhook database initialization, which can
  increase latency/locking; moving them exclusively to deployment needs a separate
  migration rollout strategy.
- Admin credentials have no application-level lockout/rate limiter, and previously
  disclosed tokens require revocation by their owner. This review cannot confirm
  revocation from repository contents.
- A separate Python dependency vulnerability scan and independent security review
  remain advisable. Copyright permissions for film excerpts remain an operator
  responsibility.
