# SubFlow — Multi-Tenant Subscription Billing Engine on Nomba

SubFlow is a multi-tenant subscription billing engine built on Nomba's payment infrastructure, purpose-built for Nigerian SaaS and subscription businesses. It owns the full subscription lifecycle — plans, virtual-account-based collection, automated dunning, proration, and instant per-transaction payouts — while Nomba handles the actual movement of money.

Beyond replicating existing billing tooling, SubFlow introduces **Save-to-Subscribe**: subscribers can pay in flexible partial deposits rather than one lump sum on a fixed due date, matching how income actually arrives for a large share of the market — a pattern not offered by Stripe, Paystack Billing, Flutterwave, or any other billing engine we looked at.

| | |
|---|---|
| **Live Demo (frontend)** | https://subflow-frontend-coral.vercel.app |
| **Live API (backend)** | https://nomba-subscriptions-engine.onrender.com |
| **Interactive API Docs** | https://nomba-subscriptions-engine.onrender.com/docs |
| **Backend Repo** | https://github.com/emmyfly/nomba-subscriptions-engine |
| **Frontend Repo** | https://github.com/emmyfly/subflow-frontend |
| **Architecture & Security Note** | [ARCHITECTURE.md](./ARCHITECTURE.md) |

> Render's free tier spins the backend down after inactivity — the first request after idle time can take 30–50 seconds to wake it up. This is infrastructure behavior, not application latency.

---

## Table of Contents

- [The Problem](#the-problem)
- [How It Works](#how-it-works)
- [What Makes SubFlow Different](#what-makes-subflow-different)
- [Architecture](#architecture)
- [Nomba Integration Depth](#nomba-integration-depth)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Getting Started Locally](#getting-started-locally)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Submission](#submission)

---

## The Problem

Nigerian SaaS and subscription businesses need recurring billing, but the usual answers don't fit:

- **Stripe / Chargebee-style billing engines** assume card-based, pull-based payments and don't integrate with Nigerian bank rails at all.
- **Nomba** (and providers like it) gives you the payment primitives — virtual accounts, transfers, webhooks — but no subscription layer on top: no plan management, no dunning, no proration, no recurring billing state machine.
- **Every billing engine we found, anywhere, assumes one full payment on a fixed due date.** That assumption doesn't hold for a large share of the market, where income is irregular and arrives in installments, not predictable monthly lump sums.

SubFlow bridges the first two gaps and directly addresses the third with Save-to-Subscribe.

## How It Works

SubFlow sits between a business's own software and Nomba. The business calls SubFlow's REST API; SubFlow calls Nomba's API; the business's customers never need to know Nomba is involved at all.

1. A business registers as a **tenant** and creates **plans**.
2. Each of that business's customers becomes a **subscriber**, and receives their own dedicated **Nomba virtual account** — a bank account number unique to them.
3. The subscriber transfers money into their account, on their own schedule, in any number of deposits.
4. Nomba notifies SubFlow via webhook the instant money lands; SubFlow identifies exactly who paid (by account number, not by asking anyone to enter a reference code) and updates their subscription state.
5. The moment a payment is confirmed, SubFlow **instantly transfers the tenant's share** (net of a platform fee) to the tenant's own bank account — no batching, no manual settlement run.
6. If a subscriber doesn't have enough deposited yet, nothing breaks — their balance just keeps accumulating until it's enough, at which point the cycle completes automatically (Save-to-Subscribe).
7. If a subscriber misses a payment entirely, an hourly job escalates them through a dunning sequence (first notice → retry → suspension), with each step logged and each subscriber's status updated automatically.

## What Makes SubFlow Different

- **Save-to-Subscribe** — partial, accumulating payments toward a billing cycle, instead of requiring one lump sum. See [Features](#features) for the full mechanics.
- **Instant, automated payouts** — not a nightly or weekly settlement batch; a tenant gets paid the moment their customer's payment clears, protected by a deterministic idempotency key so a retried payout can never double-transfer.
- **Bank-account-name verification** — before a tenant's first automatic payout, SubFlow checks Nomba's own record of who the bank account actually belongs to and holds a mismatch for manual review, rather than blindly trusting a self-reported account number.
- **Tenant-scoped invoice numbers** — every payment gets a friendly reference like `GYM-0001`, numbered per-tenant like real bookkeeping, not off one shared global counter.
- **Outgoing webhooks** — a tenant's own software gets notified the instant one of their subscribers pays or fails to pay, instead of having to poll SubFlow's API.
- **A rigorously diagnosed, transparently documented external limitation** — see [Known Limitations](#known-limitations). We didn't guess at the cause of a Nomba sandbox connectivity issue; we isolated it with a controlled, reproducible test.

## Architecture

SubFlow owns subscription state; Nomba owns money movement. The backend is a single FastAPI service backed by PostgreSQL; the frontend is a separate React/Vite/Tailwind admin dashboard, communicating with the backend purely over REST.

```
┌──────────────────┐      REST API      ┌───────────────────────────┐
│  Tenant's own     │ ─────────────────▶ │        SubFlow            │
│  software /       │                    │  (FastAPI + PostgreSQL)   │
│  Admin Dashboard  │ ◀───────────────── │                           │
└──────────────────┘   outgoing webhook  │  Tenants · Plans          │
                        (payment events)  │  Subscribers · Payments   │
                                          │  Payouts · Dunning        │
                                          └─────────────┬─────────────┘
                                                         │
                                         Nomba API (auth, virtual        ▲
                                         accounts, transfers, lookup)    │
                                                         │      Nomba webhook
                                                         ▼      (payment events)
                                          ┌───────────────────────────┐
                                          │           Nomba           │
                                          │  Virtual accounts, bank    │
                                          │  transfers, settlement     │
                                          └───────────────────────────┘
```

Money physically pools through Nomba's rails; SubFlow's database is the ledger of record for *whose* money it is, and the payout pipeline is what actually moves each tenant's share to their own bank account. Full detail — including exactly what's verified vs. what's a known gap — is in [ARCHITECTURE.md](./ARCHITECTURE.md).

## Nomba Integration Depth

SubFlow integrates a meaningful surface of Nomba's API, not just a single endpoint:

- **Authentication** — OAuth2 client-credentials flow (`POST /v1/auth/token/issue`), scoped by an `accountId` header.
- **Virtual accounts** — `POST /v1/accounts/virtual` (pooled/shared sub-account) and `POST /v1/accounts/virtual/{subAccountId}` (a tenant's own dedicated sub-account, once provisioned), so each subscriber gets a unique collection account.
- **Bank transfers** — `POST /v2/transfers/bank/{subAccountId}`, used for instant tenant payouts, with a deterministic `merchantTxRef` for idempotency.
- **Bank account lookup** — used to verify a tenant's claimed bank account name against Nomba's own record before enabling automatic payouts.
- **Incoming webhooks** — `POST /api/webhooks/nomba` parses Nomba's real payload shape (`data.transaction.aliasAccountNumber`, `data.transaction.sessionId`, etc.) and verifies the `nomba-signature`/`nomba-timestamp` headers against Nomba's documented HMAC-SHA256 scheme.

Every one of these was implemented against Nomba's actual published API reference (not guessed field names), and the two most failure-prone pieces — the real webhook payload shape and signature scheme — were specifically verified against Nomba's documentation and corrected once a discrepancy was found, rather than assumed correct because a hand-written test happened to pass.

## Features

**Core billing**
- **Multi-Tenant Isolation** — every table carries a `tenant_id`; every endpoint filters by it.
- **Subscription Plans** — monthly/quarterly/annual billing cycles with custom pricing.
- **Subscriber Management** — full lifecycle: create → activate → bill → renew → cancel.
- **Automated Billing** — tracks billing cycles and calculates next billing dates automatically.
- **Proration** — upgrading or downgrading mid-cycle calculates the credit/charge automatically (`GET /api/subscribers/{id}/proration-preview`).
- **Dunning State Machine** — failed/missed payments escalate through first notice → retry → suspension on an hourly external cron, with configurable retry intervals.

**Payments & payouts**
- **Nomba Virtual Accounts** — each subscriber gets a dedicated collection account.
- **Save-to-Subscribe** — deposits accumulate in `Subscriber.accumulated_balance` toward the current cycle's price. Once it's covered, the cycle completes, the billing date advances, and any overflow rolls forward as credit toward the next cycle — handled correctly even if one deposit happens to cover multiple cycles at once.
- **Instant, Automated Payouts** — fires inside the same webhook handler that confirms a payment, transferring the tenant's net share (after a configurable `PLATFORM_FEE_PERCENT`) to their own bank account immediately.
- **Bank-Account-Name Verification** — `verify_tenant_bank_account` fuzzy-matches (word-overlap, noise-word-stripped) a tenant's claimed name against Nomba's own account-lookup result, so "GymFlex Ltd" correctly matches "GYMFLEX NIG LIMITED" while a genuine mismatch is held for manual review instead of paid out blindly.
- **Tenant-Scoped Invoice Numbers** — `GYM-0001`, `GYM-0002`, ... — a friendly, per-tenant sequence alongside the real internal `Payment.id`.

**Security & reliability**
- **Incoming webhook idempotency** — duplicate deliveries (which every real webhook provider can send) are detected by `nomba_transaction_ref` and safely ignored, not double-processed.
- **Incoming webhook signature verification** — HMAC-SHA256 per Nomba's documented scheme, enforced whenever `NOMBA_WEBHOOK_SECRET` is configured.
- **Outgoing Webhooks** — HMAC-signed (`X-SubFlow-Signature`) notifications to a tenant's own software on `payment_succeeded`/`payment_failed`, with every delivery attempt logged (`GET /api/webhook-deliveries/`) and a failure never blocking SubFlow's own pipeline.
- **Payout idempotency** — a deterministic `merchantTxRef` per payment means a retried payout can't double-transfer.
- **Graceful external-failure handling** — every real Nomba API call is wrapped so a failure (including the geo-block described below) degrades to a clearly-labeled fallback instead of crashing the request.

**Developer & business experience**
- **Public Self-Serve Signup** — a business can register and set up payouts without any admin involvement.
- **Payment Tracking** — full payment history per subscriber, with status and payout tracking.
- **Admin Dashboard** — a separate React/Vite frontend for tenant onboarding, plan management, subscriber tracking, and payment/payout visibility.

## Tech Stack

- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL (Neon, production) — SQLite supported for local development
- **ORM:** SQLAlchemy
- **Validation:** Pydantic
- **Payments:** Nomba API (sandbox + production)
- **Scheduling:** external hourly cron (cron-job.org) calling a token-gated admin endpoint — chosen deliberately over an in-process scheduler, since Render's free tier can spin the process down between requests
- **Deployment:** Render (backend), Vercel (frontend)
- **Frontend:** React, Vite, Tailwind CSS
- **HTTP Client:** httpx (Nomba API calls)
- **Testing:** pytest, FastAPI's `TestClient`

## Project Structure

```
app/
├── main.py                     # FastAPI app, router registration, table creation
├── core/
│   ├── config.py                # Environment-driven settings
│   └── database.py              # SQLAlchemy engine/session (Postgres or SQLite)
├── models/                      # SQLAlchemy ORM models (one table each)
│   ├── tenant.py, plan.py, subscriber.py, payment.py
│   ├── payout_log.py, webhook_delivery_log.py
├── schemas/                     # Pydantic request/response schemas
├── routers/                     # One router per resource
│   ├── tenants.py, plans.py, subscribers.py, payments.py
│   ├── payouts.py, webhook_logs.py, webhooks.py, admin.py
└── services/                    # Business logic, kept out of routers
    ├── nomba.py                  # All direct Nomba API calls
    ├── nomba_webhook_security.py # Incoming webhook signature verification
    ├── outbound_webhook.py       # Outgoing webhook delivery + HMAC signing
    ├── webhook_handler.py        # Incoming webhook processing (the core pipeline)
    ├── payout.py                 # Instant payout logic
    ├── verification.py           # Bank-account-name verification
    ├── invoicing.py              # Tenant-scoped invoice numbers
    ├── billing.py                # Billing-date math, proration
    └── dunning.py                # Retry/escalation logic

tests/                           # pytest suite (concurrency + isolation tests)
scripts/                         # Demo data seed scripts
ARCHITECTURE.md                  # Full architecture & security note
```

## API Reference

### Tenants

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tenants/` | Register a new tenant (business) |
| GET | `/api/tenants/` | List all tenants |
| PUT | `/api/tenants/{id}` | Update a tenant — bank payout details, Nomba sub-account ID, webhook URL/secret |

### Plans

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/plans/` | Create a subscription plan |
| GET | `/api/plans/` | List plans (filterable by `tenant_id`) |
| GET | `/api/plans/{id}` | Get plan details |

### Subscribers

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/subscribers/` | Create subscriber + Nomba virtual account |
| GET | `/api/subscribers/` | List subscribers (filter by `tenant_id`, `status`) |
| GET | `/api/subscribers/{id}` | Get subscriber details |
| PUT | `/api/subscribers/{id}` | Update subscriber (a plan change triggers proration) |
| POST | `/api/subscribers/{id}/cancel` | Cancel a subscriber's subscription |
| GET | `/api/subscribers/{id}/proration-preview` | Preview proration cost for a plan change |
| GET | `/api/subscribers/due-for-retry` | List subscribers due for a dunning retry |

### Payments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/payments/` | List payments (filter by `tenant_id`, subscriber) |
| GET | `/api/payments/{id}` | Get payment details |

### Payouts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/payouts/` | List payout attempts (filter by `tenant_id`) |

### Webhook Deliveries

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/webhook-deliveries/` | List outgoing webhook delivery attempts (filter by `tenant_id`) |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/webhooks/nomba` | Receive Nomba payment notifications |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/admin/run-billing-check?token=...` | Runs the dunning first-notice/retry-escalation sweep; token-gated, called by an external hourly cron |

Full interactive documentation (request/response schemas, try-it-out): https://nomba-subscriptions-engine.onrender.com/docs

## Getting Started Locally

```bash
# Clone
git clone https://github.com/emmyfly/nomba-subscriptions-engine.git
cd nomba-subscriptions-engine

# Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export NOMBA_CLIENT_ID=your_client_id
export NOMBA_CLIENT_SECRET=your_client_secret
export NOMBA_ACCOUNT_ID=your_parent_account_id
export NOMBA_SUBACCOUNT_ID=your_subaccount_id        # optional -- pooled fallback if unset
export NOMBA_BASE_URL=https://sandbox.nomba.com
export NOMBA_WEBHOOK_SECRET=your_webhook_signing_key # optional -- see ARCHITECTURE.md
export CRON_TOKEN=any_random_string                  # gates /api/admin/run-billing-check
export PLATFORM_FEE_PERCENT=3.0                      # optional, defaults to 3.0
export DATABASE_URL=sqlite:///./subscription.db      # or a postgresql:// URL

# Run
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API documentation.

Demo data can be seeded via the scripts in `scripts/` (`seed_demo_data.py` for tenants/subscribers, `seed_demo_payments.py` for a realistic mix of successful/past-due/recovered payments).

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

The suite includes a concurrency test that fires ten simultaneous subscriber-creation requests and verifies no collisions and correct tenant isolation under load.

## Deployment

- **Backend:** Render (free tier), auto-deploying from `main` on push. Environment variables configured in Render's dashboard.
- **Database:** Neon (serverless PostgreSQL) — chosen for persistence across deploys, since Render's free-tier filesystem is ephemeral and a local SQLite file would otherwise reset on every redeploy.
- **Frontend:** Vercel, auto-deploying from the frontend repo.
- **Scheduled billing checks:** an external cron (cron-job.org) calls `POST /api/admin/run-billing-check` hourly — a deliberate choice over an in-process scheduler, since Render's free tier can spin the process down between requests, silently stopping any in-process timer.

## Known Limitations

**Nomba's sandbox blocks this deployment's IP at the authentication layer.** Confirmed via a controlled, reproducible test: identical credentials and an identical request succeed when run from a Nigerian IP, and return `403 Forbidden` when run from this Render-hosted backend (Ohio, US) — isolated specifically to the `POST /v1/auth/token/issue` call, before any account-scoping logic is even reached. This has been reported to the Nomba team; no response yet as of submission.

SubFlow includes a transparent fallback so the full subscriber lifecycle — creation, billing, webhook processing, payouts — remains fully testable end-to-end regardless of this external constraint. When a real Nomba API call fails, the system generates a clearly-labeled mock virtual account (`mock_...` prefix) rather than silently failing or faking success.

Two further limitations, disclosed in full in [ARCHITECTURE.md](./ARCHITECTURE.md):
- A tenant's `api_key` is issued at registration but not yet enforced as request-level authentication on standard CRUD endpoints.
- Bank details and webhook secrets rely on the database host's storage-level encryption, not application-level field encryption.

## Roadmap

- **Multi-provider abstraction** — support banks/processors beyond Nomba, behind a common interface.
- **Group/pooled subscriptions** — multiple people splitting the cost of one shared subscription slot, an "ajo for subscriptions" model.
- **Diaspora billing** — letting a relative abroad pay a local subscriber's bill directly.
- **Native Nomba onboarding integration** — removing the manual sub-account provisioning step entirely, for businesses onboarded directly through Nomba rather than as an external platform integration.
- **Tenant API key enforcement** — closing the authentication gap disclosed above.

## Submission

Built for the Nomba x DevCareer Hackathon 2026.

**Author:** Emmanuel Olumide Akerele
**GitHub:** [@emmyfly](https://github.com/emmyfly)
