# SubFlow — Multi-Tenant Subscription Engine

A production-ready subscription management engine built on Nomba's payment infrastructure. SubFlow enables SaaS businesses to manage recurring billing, subscriber lifecycle, plan changes with proration, and automated dunning — all through a clean REST API.

**Live API:** https://nomba-subscriptions-engine.onrender.com  
**API Docs:** https://nomba-subscriptions-engine.onrender.com/docs  
**GitHub:** https://github.com/emmyfly/nomba-subscriptions-engine

## The Problem

Nigerian SaaS businesses need subscription billing but existing solutions (Stripe, Chargebee) don't integrate with local payment rails. Nomba provides the payment infrastructure, but there's no plug-and-play subscription layer on top of it. SubFlow bridges that gap.

## How It Works

SubFlow sits between your application and Nomba. It manages the subscription logic — plans, billing cycles, upgrades/downgrades, failed payment retries — while Nomba handles the actual money movement via virtual accounts.
## Features

- **Multi-Tenant Isolation** — Each business (tenant) gets isolated data. All endpoints filter by `tenant_id`.
- **Subscription Plans** — Create monthly/yearly plans with custom pricing. Plans support metadata for feature flags.
- **Subscriber Management** — Full lifecycle: create subscriber → assign plan → activate → bill → renew/cancel.
- **Nomba Virtual Accounts** — Each subscriber gets a dedicated virtual account via Nomba's API for payment collection.
- **Automated Billing** — Track billing cycles, calculate next billing dates, process renewals.
- **Proration** — When subscribers upgrade or downgrade mid-cycle, SubFlow calculates the credit/charge automatically.
- **Dunning State Machine** — Failed payments trigger escalating retry logic (retry queue with configurable intervals).
- **Webhook Processing** — Receives and validates Nomba payment webhooks to confirm transactions in real-time.
- **Payment Tracking** — Full payment history per subscriber with status tracking.

## Tech Stack

- **Framework:** FastAPI (Python)
- **Database:** SQLite (dev) / PostgreSQL (production-ready via SQLAlchemy)
- **ORM:** SQLAlchemy
- **Validation:** Pydantic
- **Payments:** Nomba API (sandbox + production)
- **Deployment:** Render
- **HTTP Client:** httpx (async Nomba API calls)

## API Endpoints

### Tenants
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tenants/` | Register a new tenant (business) |
| GET | `/api/tenants/` | List all tenants |

### Plans
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/plans/` | Create a subscription plan |
| GET | `/api/plans/` | List plans (filterable by tenant_id) |
| GET | `/api/plans/{id}` | Get plan details |

### Subscribers
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/subscribers/` | Create subscriber + Nomba virtual account |
| GET | `/api/subscribers/` | List subscribers (filter by tenant_id, status) |
| GET | `/api/subscribers/{id}` | Get subscriber details |
| PUT | `/api/subscribers/{id}` | Update subscriber (change plan triggers proration) |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/payments/` | List payments (filter by tenant_id, subscriber) |
| GET | `/api/payments/{id}` | Get payment details |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/webhooks/nomba` | Receive Nomba payment notifications |

## Quick Start

```bash
# Clone
git clone https://github.com/emmyfly/nomba-subscriptions-engine.git
cd nomba-subscriptions-engine

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export NOMBA_CLIENT_ID=your_client_id
export NOMBA_CLIENT_SECRET=your_client_secret
export NOMBA_ACCOUNT_ID=your_account_id

# Run
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for the interactive API documentation.

## Architecture
## Submission

Built for the **Nomba x DevCareer Hackathon 2026**.

**Author:** Emmanuel Olumide Akerele  
**GitHub:** [@emmyfly](https://github.com/emmyfly)
