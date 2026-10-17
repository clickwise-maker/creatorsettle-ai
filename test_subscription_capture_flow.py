"""
Integration tests for subscription-capture approval flow.
PayPal capture is always mocked: these tests never move money.
"""
from pathlib import Path
from unittest.mock import patch

from backend import app


def clean():
    Path("approvals.json").unlink(missing_ok=True)
    Path("approvals.json.tmp").unlink(missing_ok=True)


def test_requires_approval_and_executes_once():
    clean()
    client = app.test_client()
    with patch("creatorsettle_execution.capture_outstanding_balance", return_value={
        "success": True, "state": "CAPTURE_CONFIRMED", "reason": "capture_confirmed",
        "status_code": 201, "raw": {"status": "COMPLETED", "id": "CAP-TEST"},
    }) as capture:
        response = client.post("/api/subscription-capture/propose", json={
            "subscription_id": "I-TEST12345", "amount": "12.50", "currency": "USD"
        })
        assert response.status_code == 200
        request_data = response.get_json()
        request_id = request_data["request_id"]
        assert request_data["status"] == "PENDING"

        # Unapproved execution must be blocked and must not call PayPal.
        blocked = client.post(f"/api/subscription-capture/execute/{request_id}")
        assert blocked.status_code == 409
        assert blocked.get_json()["state"] == "BLOCKED"
        capture.assert_not_called()

        approved = client.post(f"/api/subscription-capture/approve/{request_id}")
        assert approved.get_json()["status"] == "APPROVED"

        result = client.post(f"/api/subscription-capture/execute/{request_id}")
        assert result.status_code == 200
        assert result.get_json()["state"] == "CAPTURE_CONFIRMED"
        capture.assert_called_once_with("I-TEST12345", "12.50", "USD", note=f"CreatorSettle approval {request_id}", request_id=request_id)

        # Duplicate execution must be blocked, no second capture.
        duplicate = client.post(f"/api/subscription-capture/execute/{request_id}")
        assert duplicate.status_code == 409
        capture.assert_called_once()


def test_rejected_request_never_calls_paypal():
    clean()
    client = app.test_client()
    with patch("creatorsettle_execution.capture_outstanding_balance") as capture:
        proposed = client.post("/api/subscription-capture/propose", json={
            "subscription_id": "I-TEST67890", "amount": "5.00", "currency": "USD"
        }).get_json()
        request_id = proposed["request_id"]
        rejected = client.post(f"/api/subscription-capture/reject/{request_id}")
        assert rejected.get_json()["status"] == "REJECTED"
        result = client.post(f"/api/subscription-capture/execute/{request_id}")
        assert result.status_code == 409
        capture.assert_not_called()


def test_invalid_proposal_rejected():
    clean()
    client = app.test_client()
    response = client.post("/api/subscription-capture/propose", json={
        "subscription_id": "bad", "amount": "20.00", "currency": "USD"
    })
    assert response.status_code == 400
    assert response.get_json()["status"] == "BLOCKED"


if __name__ == "__main__":
    for test in (
        test_requires_approval_and_executes_once,
        test_rejected_request_never_calls_paypal,
        test_invalid_proposal_rejected,
    ):
        test()
        print(f"PASS {test.__name__}")
    clean()
    print("All subscription flow tests passed; PayPal network call mocked.")
