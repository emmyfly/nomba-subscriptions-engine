# SubFlow — Architecture & Security Note

## Overview

SubFlow is a multi-tenant subscription billing engine (FastAPI + PostgreSQL) sitting between a business's software and Nomba's payment rails. It owns subscription state — plans, billing cycles, dunning, proration — and delegates money movement to Nomba via dedicated virtual accounts (collection) and bank transfers (payout).

Core entities: `Tenant` (a business), `Plan`, `Subscriber` (a tenant's customer), `Payment`, `PayoutLog`, `WebhookDeliveryLog`.

## Authentication

**SubFlow → Nomba.** OAuth2 client-credentials flow (`POST /v1/auth/token/issue`) using `NOMBA_CLIENT_ID`/`NOMBA_CLIENT_SECRET`, scoped by an `accountId` header (the parent business account). Virtual-account and transfer calls additionally scope to a specific sub-account via the URL path when a tenant has their own `nomba_subaccount_id`; otherwise they fall back to one shared pooled sub-account, so a tenant can start collecting payments without waiting on Nomba's (currently API-less, dashboard-only) sub-account provisioning process.

**Tenant-facing API.** Each tenant is issued an `api_key` at registration. **Known limitation, disclosed rather than hidden:** this key is not yet enforced as a bearer-auth check on standard CRUD endpoints — `tenant_id` is currently a caller-supplied value, not derived from an authenticated identity. In its current state, a caller who knows another tenant's numeric ID could read or write that tenant's data. The fix (require `Authorization: Bearer <api_key>` on tenant-scoped routes, deriving `tenant_id` server-side from the authenticated key rather than trusting the request body) is understood and scoped but not yet implemented.

**Admin/cron endpoints.** `/api/admin/run-billing-check` is gated by a shared-secret query token (`CRON_TOKEN`), checked with a constant-time-equivalent guard, appropriate for a single trusted external caller (an hourly cron job) rather than public traffic.

## Webhooks

**Incoming (Nomba → SubFlow), `POST /api/webhooks/nomba`.**
- **Idempotency:** every payload's `transaction.transactionId` is checked against already-processed payments before anything is mutated. A duplicate delivery (webhooks can and do arrive more than once from any real provider) is a no-op, not a double-charge or double-payout.
- **Signature verification:** implemented per Nomba's documented scheme — HMAC-SHA256, base64-encoded, computed over `event_type:requestId:userId:walletId:transactionId:transactionType:transactionTime:responseCode:timestamp` (not the raw body), compared using a constant-time comparison. Enforced whenever `NOMBA_WEBHOOK_SECRET` is configured; if unset, requests are still processed but a warning is logged on every request. This is disclosed, not swept under the rug: Nomba's sandbox currently blocks this deployment's IP at the auth layer (confirmed via controlled, reproducible testing — identical requests succeed from a Nigerian IP and return `403` from this Render-hosted instance), so Nomba cannot currently deliver a real, signed webhook to this deployment regardless of configuration.
- **Field-path correctness:** the real Nomba payload places the destination virtual account at `data.transaction.aliasAccountNumber` and the session at `data.transaction.sessionId` — earlier code (and every hand-crafted test payload used during development) assumed nonexistent `data.accountNumber` / `data.order.orderReference` fields. This was caught and fixed while preparing this note; a real webhook would previously have matched zero subscribers.

**Outgoing (SubFlow → tenant), fired on `payment_succeeded`/`payment_failed`.**
- Signed with HMAC-SHA256 over the JSON body using the tenant's own `webhook_secret`, sent as `X-SubFlow-Signature` — the same pattern Nomba uses toward SubFlow, so a tenant can verify a delivery genuinely came from SubFlow.
- Every attempt (success or failure, with status code and error detail) is recorded in `WebhookDeliveryLog`, queryable via `GET /api/webhook-deliveries/`.
- A delivery failure is caught and logged, never raised — a tenant's downed server cannot block SubFlow's own payment/payout pipeline.

## Data handling

- **Tenant isolation:** every core table carries a `tenant_id` foreign key; every list/query endpoint filters by it. Verified directly (not just by code inspection) with two live tenants holding distinct subscribers, payments, and payout destinations simultaneously.
- **Secrets:** Nomba API credentials live only in environment variables, never in the database or source. A tenant's `webhook_secret` is stored in the database (needed to sign outgoing deliveries) but is write-only via the API — it is never included in any API response.
- **Financial safety:** payouts are keyed by a deterministic `merchantTxRef` (`payout_{payment.id}`), so a retried payout for the same payment cannot double-transfer. Bank-account-name verification runs before a tenant's first automatic payout, holding it for manual review on a mismatch rather than silently trusting caller-supplied bank details.
- **Persistence:** PostgreSQL (Neon), not the SQLite this project started on — survives redeploys, unlike a container-local file on Render's ephemeral filesystem.
- **At-rest encryption:** bank account details and webhook secrets rely on the database host's storage-level encryption (Neon/Postgres), not application-level field encryption. Acceptable for this stage; a hardening item for a production posture beyond hackathon scope.

## Known limitations (disclosed)

1. Tenant API key exists but isn't yet enforced as request-level authentication (see above).
2. Nomba sandbox blocks this deployment's IP at the auth layer — confirmed, documented, and handled via a clearly-labeled fallback so the full subscriber lifecycle stays demoable regardless.
3. No encryption at the application layer for stored bank details/secrets — relies on the database host.
