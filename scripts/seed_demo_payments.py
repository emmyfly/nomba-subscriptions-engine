"""
Seeds payment history for an existing tenant's subscribers by simulating
Nomba webhook events (the only way payments get created — there's no direct
POST /api/payments/ endpoint by design).

Gives the demo a realistic mix instead of an all-success log:
  - most subscribers get one successful payment
  - one gets a failed payment (ends up "past_due", visible in the dunning
    retry queue)
  - one fails then recovers (shows the past_due -> active recovery path)
  - one is left untouched (a "just signed up, not billed yet" subscriber)

Usage:
    python scripts/seed_demo_payments.py --tenant-id 3
    python scripts/seed_demo_payments.py --tenant-id 3 --base-url http://localhost:8000
"""
import argparse
import secrets
import sys

import httpx

LIVE_API = "https://nomba-subscriptions-engine.onrender.com"


def send_webhook(client: httpx.Client, event_type: str, account_number: str, amount: float) -> dict:
    payload = {
        "event_type": event_type,
        "data": {
            "accountNumber": account_number,
            "transaction": {
                "transactionAmount": amount,
                "transactionId": f"txn_{secrets.token_hex(8)}",
            },
            "order": {"orderReference": f"order_{secrets.token_hex(8)}"},
        },
    }
    resp = client.post("/api/webhooks/nomba", json=payload)
    resp.raise_for_status()
    return resp.json()


def seed(base_url: str, tenant_id: int) -> None:
    with httpx.Client(base_url=base_url, timeout=15) as client:
        resp = client.get("/api/subscribers/", params={"tenant_id": tenant_id, "status": "active"})
        resp.raise_for_status()
        subscribers = resp.json()

        if not subscribers:
            print(f"No active subscribers found for tenant {tenant_id}. Seed subscribers first.")
            sys.exit(1)

        print(f"Found {len(subscribers)} active subscribers for tenant {tenant_id}.\n")

        if len(subscribers) < 3:
            # Not enough subscribers for the full success/past-due/recovered mix —
            # just mark everyone as paid.
            for sub in subscribers:
                result = send_webhook(client, "payment_success", sub["nomba_account_number"], sub["amount"])
                print(f"  paid      {sub['name']:<16} -> {result['detail']}")
            print("\nDone.")
            return

        untouched = subscribers[-1]
        recovered = subscribers[-2]
        past_due = subscribers[-3]
        successes = subscribers[:-3]

        for sub in successes:
            result = send_webhook(client, "payment_success", sub["nomba_account_number"], sub["amount"])
            print(f"  paid      {sub['name']:<16} -> {result['detail']}")

        result = send_webhook(client, "payment_failed", past_due["nomba_account_number"], past_due["amount"])
        print(f"  failed    {past_due['name']:<16} -> {result['detail']}")

        result = send_webhook(client, "payment_failed", recovered["nomba_account_number"], recovered["amount"])
        print(f"  failed    {recovered['name']:<16} -> {result['detail']}")
        result = send_webhook(client, "payment_success", recovered["nomba_account_number"], recovered["amount"])
        print(f"  recovered {recovered['name']:<16} -> {result['detail']}")

        print(f"  untouched {untouched['name']:<16} -> left as never-billed")

        print("\nDone.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", type=int, required=True, help="Tenant to seed payments for")
    parser.add_argument(
        "--base-url",
        default=LIVE_API,
        help=f"API base URL (default: live demo at {LIVE_API})",
    )
    args = parser.parse_args()

    try:
        seed(args.base_url, args.tenant_id)
    except httpx.HTTPStatusError as e:
        print(f"Request failed: {e.response.status_code} {e.response.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
