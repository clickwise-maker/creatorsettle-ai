"""
CreatorSettle AI — Tests
"""

import os
from pathlib import Path

def clean():
    for f in ["audit.jsonl", "approvals.json"]:
        Path(f).unlink(missing_ok=True)

def test_decision():
    print("=== Decision Engine Test ===")
    from creatorsettle_decision import decide
    cases = [
        ({"decline_code": "INSUFFICIENT_FUNDS", "retry_count": 0}, "ROUTE"),
        ({"decline_code": "INSUFFICIENT_FUNDS", "retry_count": 2}, "ESCALATE"),
        ({"decline_code": "EXPIRED_CARD", "retry_count": 0}, "ESCALATE"),
        ({"decline_code": None, "retry_count": 0}, "HOLD"),
        ({"decline_code": "FAILED", "retry_count": 0}, "RETRY"),
    ]
    for txn, expected in cases:
        action, conf, msg, exec_type = decide(txn)
        assert action == expected, f"Expected {expected}, got {action} for {txn}"
        assert exec_type in ("api", "instruction", "none")
    print("PASS")

def test_approval_gate():
    print("\n=== Approval Gate Test ===")
    from creatorsettle_approval import propose, decide as approval_decide
    clean()
    propose("TXN-GATE", "RETRY", "test")
    # No approval yet
    assert approval_decide("TXN-GATE", "APPROVE") == "APPROVED"
    assert approval_decide("TXN-GATE", "APPROVE") == "APPROVED"  # already decided
    print("PASS")

def test_audit_and_tamper():
    print("\n=== Audit + Tamper Test ===")
    from creatorsettle_audit import append, verify, test_tamper
    clean()
    append({"txn_id": "T1", "action": "RETRY"})
    append({"txn_id": "T2", "action": "ESCALATE"})
    assert verify() is True
    # test_tamper should detect and we clean after
    detected = test_tamper()
    assert detected is True
    # Clean up after tamper test
    clean()
    append({"txn_id": "CLEAN", "action": "HOLD"})
    assert verify() is True
    print("PASS")

def test_oauth_mock():
    print("\n=== OAuth / Mock Test ===")
    from creatorsettle_reader import get_access_token, fetch_failed_transactions
    token = get_access_token()
    txns = fetch_failed_transactions(token)
    assert len(txns) > 0
    print(f"Source: {txns[0].get('source')}")
    print("PASS")

if __name__ == "__main__":
    clean()
    test_decision()
    test_approval_gate()
    test_audit_and_tamper()
    test_oauth_mock()
    print("\n=== All tests passed ===")
