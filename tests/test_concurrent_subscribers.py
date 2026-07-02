"""
Simulates 10 active users hitting the API at once to verify subscriber
creation is safe under concurrency and tenant isolation holds.

Uses a throwaway SQLite file so it never touches the dev/production
subscription.db. The DATABASE_URL env var must be set before app.core.database
is imported, since the engine is created at import time.
"""
import concurrent.futures
import os
import tempfile

TEST_DB_PATH = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_db():
    yield
    os.remove(TEST_DB_PATH)


def _create_tenant_and_plan():
    tenant_resp = client.post(
        "/api/tenants/", json={"name": "LoadTest Co", "email": "loadtest@example.com"}
    )
    assert tenant_resp.status_code == 201, tenant_resp.text
    tenant_id = tenant_resp.json()["id"]

    plan_resp = client.post(
        "/api/plans/",
        json={
            "tenant_id": tenant_id,
            "name": "Pro Monthly",
            "price": 5000,
            "billing_cycle": "monthly",
        },
    )
    assert plan_resp.status_code == 201, plan_resp.text
    plan_id = plan_resp.json()["id"]

    return tenant_id, plan_id


def test_ten_concurrent_active_users():
    tenant_id, plan_id = _create_tenant_and_plan()

    def create_subscriber(i: int):
        return client.post(
            "/api/subscribers/",
            json={
                "tenant_id": tenant_id,
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "plan_id": plan_id,
            },
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        responses = list(pool.map(create_subscriber, range(10)))

    assert [r.status_code for r in responses] == [201] * 10
    bodies = [r.json() for r in responses]

    assert all(b["status"] == "active" for b in bodies)
    assert all(b["tenant_id"] == tenant_id for b in bodies)

    # No two concurrent requests should collide on the same virtual account.
    account_ids = {b["nomba_virtual_account_id"] for b in bodies}
    assert len(account_ids) == 10

    list_resp = client.get(
        "/api/subscribers/", params={"tenant_id": tenant_id, "status": "active"}
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 10


def test_other_tenants_do_not_see_these_subscribers():
    other_tenant_resp = client.post(
        "/api/tenants/", json={"name": "Other Co", "email": "other@example.com"}
    )
    other_tenant_id = other_tenant_resp.json()["id"]

    list_resp = client.get(
        "/api/subscribers/", params={"tenant_id": other_tenant_id, "status": "active"}
    )
    assert list_resp.status_code == 200
    assert list_resp.json() == []
