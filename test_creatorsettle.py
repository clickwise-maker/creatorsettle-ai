"""
CreatorSettle AI — Tests
All cases actually executed.
"""

from pathlib import Path
from creatorsettle_decision import decide
from creatorsettle_approval import propose, decide as approval_decide, get_status
from creatorsettle_execution import execute_action
from creatorsettle_audit import append, verify, test_tamper
from creatorsettle_reader import fetch_failed_transactions

def clean():
    for f in ["audit.jsonl", "approvals.json"]:
        Path(f).unlink(missing_ok=True)

def test_decision_honest():
    print("=== Decision (honest, no invented reasons) ===")
    cases = [
        ({"decline_code": "DENIED", "retry_count": 0, "source": "mock"}, "RETRY", "instruction"),
        ({"decline_code": "FAILED", "retry_count": 1, "source": "real"}, "ESCALATE", "instruction"),
        ({"decline_code": "PENDING", "retry_count": 0}, "HOLD", "none"),
        ({"decline_code": None, "retry_count": 0}, "HOLD", "instruction"),
    ]
    for txn, exp_action, exp_type in cases:
        action, _, msg, exec_type = decide(txn)
        assert action == exp_action, f"got {action}"
        assert exec_type == exp_type
        assert "INSUFFICIENT_FUNDS" not in msg  # never invented
    print("PASS")

def test_approval_blocks_execution():
    print("\n=== Approval blocks execution ===")
    clean()
    propose("T1", "RETRY", "test")
    # No approval
    r = execute_action("T1", "RETRY", "instruction")
    assert not r["executed"]
    assert "blocked" in r["reason"]
    print("No-approval blocked: PASS")

    # Rejected
    approval_decide("T1", "REJECT")
    r = execute_action("T1", "RETRY", "instruction")
    assert not r["executed"]
    assert "REJECTED" in r["reason"] or "blocked" in r["reason"]
    print("Rejected blocked: PASS")

    # Expired (manual)
    propose("T2", "RETRY", "test", expires_minutes=-1)
    r = execute_action("T2", "RETRY", "instruction")
    assert not r["executed"]
    print("Expired blocked: PASS")

def test_duplicate_blocked():
    print("\n=== Duplicate execution blocked ===")
    clean()
    propose("T3", "RETRY", "test")
    approval_decide("T3", "APPROVE")
    r1 = execute_action("T3", "RETRY", "instruction")
    assert r1["executed"]
    r2 = execute_action("T3", "RETRY", "instruction")
    assert not r2["executed"]
    assert "duplicate" in r2["reason"]
    print("PASS")

def test_mock_vs_real_label():
    print("\n=== Mock vs real labeling ===")
    mock = fetch_failed_transactions(None)
    assert all(t["source"] == "mock" for t in mock)
    assert all(t["decline_code"] in ("DENIED", "FAILED", "PENDING") for t in mock)
    print("PASS")

def test_audit_tamper_and_cleanup():
    print("\n=== Audit tamper + cleanup ===")
    clean()
    append({"txn_id": "A1", "action": "HOLD"})
    assert verify()
    assert test_tamper() is True
    # After test_tamper the file is restored
    assert verify()
    print("PASS")

def test_verification_unavailable():
    print("\n=== Verification unavailable ===")
    clean()
    propose("T4", "RETRY", "test")
    approval_decide("T4", "APPROVE")
    r = execute_action("T4", "RETRY", "instruction", access_token="fake")
    assert r["executed"]
    assert r["verification"] is None  # cannot re-fetch
    print("PASS")

if __name__ == "__main__":
    clean()
    test_decision_honest()
    test_approval_blocks_execution()
    test_duplicate_blocked()
    test_mock_vs_real_label()
    test_audit_tamper_and_cleanup()
    test_verification_unavailable()
    clean()
    print("\n=== All tests passed ===")
