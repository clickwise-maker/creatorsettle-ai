"""
CreatorSettle AI — Tests (including backend integration)
"""

from pathlib import Path
from creatorsettle_decision import decide
from creatorsettle_approval import propose, decide as approval_decide, get_status
from creatorsettle_execution import execute_action
from creatorsettle_audit import append, verify, test_tamper
from creatorsettle_reader import fetch_failed_transactions
from backend import app

def clean():
    for f in ["audit.jsonl", "approvals.json"]:
        Path(f).unlink(missing_ok=True)

def test_decision_honest():
    print("=== Decision (honest) ===")
    cases = [
        ({"decline_code": "DENIED", "retry_count": 0, "source": "mock"}, "RETRY", "instruction"),
        ({"decline_code": "FAILED", "retry_count": 1, "source": "real"}, "ESCALATE", "instruction"),
        ({"decline_code": "PENDING", "retry_count": 0}, "HOLD", "none"),
        ({"decline_code": None, "retry_count": 0}, "HOLD", "instruction"),
    ]
    for txn, exp_action, exp_type in cases:
        action, _, msg, exec_type = decide(txn)
        assert action == exp_action
        assert exec_type == exp_type
        assert "INSUFFICIENT_FUNDS" not in msg
    print("PASS")

def test_propose_does_not_reset():
    print("\n=== propose() does not reset decided records ===")
    clean()
    propose("T1", "RETRY", "first")
    approval_decide("T1", "APPROVE")
    status = propose("T1", "RETRY", "second")
    assert status == "APPROVED"
    assert get_status("T1") == "APPROVED"
    print("PASS")

def test_approval_blocks():
    print("\n=== Approval blocks ===")
    clean()
    propose("T1", "RETRY", "test")
    r = execute_action("T1")
    assert not r["executed"]
    approval_decide("T1", "REJECT")
    r = execute_action("T1")
    assert not r["executed"]
    propose("T2", "RETRY", "test", expires_minutes=-1)
    r = execute_action("T2")
    assert not r["executed"]
    print("PASS")

def test_duplicate_blocked():
    print("\n=== Duplicate blocked ===")
    clean()
    propose("T3", "RETRY", "test")
    approval_decide("T3", "APPROVE")
    r1 = execute_action("T3")
    assert r1["executed"]
    r2 = execute_action("T3")
    assert not r2["executed"]
    # Re-propose should not reset
    propose("T3", "RETRY", "again")
    r3 = execute_action("T3")
    assert not r3["executed"]
    print("PASS")

def test_backend_integration():
    print("\n=== Backend integration (Flask test client) ===")
    clean()
    client = app.test_client()

    # Transactions
    rv = client.get("/api/transactions")
    assert rv.status_code == 200
    txns = rv.get_json()
    assert len(txns) > 0

    tid = txns[0]["id"]

    # Propose
    rv = client.post(f"/api/propose/{tid}", json={"action": "RETRY", "message": "test"})
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "PENDING"

    # Reject
    rv = client.post(f"/api/reject/{tid}")
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "REJECTED"

    # Execute should be blocked
    rv = client.post(f"/api/execute/{tid}")
    data = rv.get_json()
    assert not data["executed"]

    # New txn approve + execute
    clean()
    rv = client.post("/api/propose/NEW1", json={"action": "RETRY"})
    assert rv.get_json()["status"] == "PENDING"
    rv = client.post("/api/approve/NEW1")
    assert rv.get_json()["status"] == "APPROVED"
    rv = client.post("/api/execute/NEW1")
    data = rv.get_json()
    assert data["executed"]
    assert "instruction_given" in data["reason"]

    # Duplicate
    rv = client.post("/api/execute/NEW1")
    assert not rv.get_json()["executed"]

    # Malformed
    rv = client.post("/api/approve/NONEXISTENT")
    assert rv.status_code == 400

    print("PASS")

def test_mock_label():
    print("\n=== Mock labeling ===")
    mock = fetch_failed_transactions(None)
    assert all(t["source"] == "mock" for t in mock)
    print("PASS")

def test_audit():
    print("\n=== Audit ===")
    clean()
    append({"txn_id": "A1", "action": "HOLD"})
    assert verify()
    assert test_tamper() is True
    assert verify()
    print("PASS")

if __name__ == "__main__":
    clean()
    test_decision_honest()
    test_propose_does_not_reset()
    test_approval_blocks()
    test_duplicate_blocked()
    test_backend_integration()
    test_mock_label()
    test_audit()
    clean()
    print("\n=== All tests passed ===")
