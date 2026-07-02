"""
Seeds a running SubFlow instance with a demo tenant, one plan, and 10 active
subscribers, so the admin dashboard has something to show.

Talks to the API over HTTP, so it works against either a local server or the
live Render deployment.

Usage:
    python scripts/seed_demo_data.py
    python scripts/seed_demo_data.py --base-url http://localhost:8000
"""
import argparse
import sys

import httpx

LIVE_API = "https://nomba-subscriptions-engine.onrender.com"

CUSTOMERS = [
    ("Ada Obi", "ada.obi@example.com"),
    ("Chidi Nwosu", "chidi.nwosu@example.com"),
    ("Bisi Adeyemi", "bisi.adeyemi@example.com"),
    ("Tunde Bakare", "tunde.bakare@example.com"),
    ("Ngozi Eze", "ngozi.eze@example.com"),
    ("Femi Ogundipe", "femi.ogundipe@example.com"),
    ("Zainab Musa", "zainab.musa@example.com"),
    ("Kelechi Umeh", "kelechi.umeh@example.com"),
    ("Amara Chukwu", "amara.chukwu@example.com"),
    ("Segun Alabi", "segun.alabi@example.com"),
]


def seed(base_url: str) -> None:
    with httpx.Client(base_url=base_url, timeout=15) as client:
        tenant_resp = client.post(
            "/api/tenants/",
            json={"name": "Demo SaaS Inc", "email": "billing@demosaas.com"},
        )
        tenant_resp.raise_for_status()
        tenant = tenant_resp.json()
        print(f"Created tenant: {tenant['name']} (id={tenant['id']})")

        plan_resp = client.post(
            "/api/plans/",
            json={
                "tenant_id": tenant["id"],
                "name": "Pro Monthly",
                "description": "Full access, billed monthly",
                "price": 5000,
                "billing_cycle": "monthly",
            },
        )
        plan_resp.raise_for_status()
        plan = plan_resp.json()
        print(f"Created plan: {plan['name']} (id={plan['id']}, NGN {plan['price']}/mo)")

        created = 0
        for name, email in CUSTOMERS:
            sub_resp = client.post(
                "/api/subscribers/",
                json={
                    "tenant_id": tenant["id"],
                    "name": name,
                    "email": email,
                    "plan_id": plan["id"],
                },
            )
            if sub_resp.status_code != 201:
                print(f"  FAILED  {name}: {sub_resp.status_code} {sub_resp.text}")
                continue
            sub = sub_resp.json()
            created += 1
            print(f"  created  {sub['name']:<16} status={sub['status']:<8} account={sub['nomba_virtual_account_id']}")

        print(f"\nDone: {created}/{len(CUSTOMERS)} active subscribers created for tenant {tenant['id']}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=LIVE_API,
        help=f"API base URL to seed (default: live demo at {LIVE_API})",
    )
    args = parser.parse_args()

    try:
        seed(args.base_url)
    except httpx.HTTPStatusError as e:
        print(f"Request failed: {e.response.status_code} {e.response.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
