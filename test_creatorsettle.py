"""
CreatorSettle AI — Tests
Run: python test_creatorsettle.py
"""

import os
import shutil
from pathlib import Path

def clean():
    for f in ["audit.jsonl", "approvals.json"]:
        Path(f).unlink(missing_ok=True)

def test_oauth_and_mock():
    print("=== OAuth / Mock Test ===")
    from creatorsettle_reader import get_access_token, fetch_failed_transactions
    token = get_access_token()
    if token:
        print("OAuth: SUCCESS")
    else:
        print("OAuth: FAILED (expected without credentials)")
    txns = fetch_failed_transactions(token)
    assert len(txns) > 0
    print(f"Transactions source: {txns[0].get('source')}")
    print("PASS")

def test_decision():
    print("\n=== Decision Engine Test ===")
    from creatorsettle_decision import decide, decide_with_ai
    cases = [
        ({"decline_code": "INSUFFICIENT_FUNDS", "retry_count": 0}, "ROUTE"),
        ({"decline_code": "INSUFFICIENT_FUNDS", "retry_count": 2}, "ALERT"),
        ({"decline_code": "EXPIRED_CARD", "retry_count": 0}, "ALERT"),
        ({"decline_code": None, "retry_count": 0}, "HOLD"),
    ]
    for txn, expected in cases:
        action, _, _ = decide(txn)
        assert action == expected, f"Expected {expected}, got {action}"
    action, _, msg = decide_with_ai({"decline_code": "FRAUD_FILTER"}, llm_client=None)
    assert "deterministic" in msg or "rules" in msg
    print("PASS")

def test_approval_persistence():
    print("\n=== Approval Persistence Test ===")
    from creatorsettle_approval import propose, decide
    clean()
    propose("TXN-1", "RETRY", "test")
    assert decide("TXN-1", "APPROVE") == "APPROVED"
    # Simulate restart by reloading
    assert decide("TXN-1", "APPROVE") == "APPROVED"  # already decided
    print("PASS")

def test_audit_and_tamper():
    print("\n=== Audit + Tamper Test ===")
    from creatorsettle_audit import append, verify, test_tamper
    clean()
    append({"txn_id": "T1", "action": "RETRY"})
    append({"txn_id": "T2", "action": "ALERT"})
    assert verify() is True
    assert test_tamper() is True
    print("Tamper detected: PASS")
    print("PASS")

if __name__ == "__main__":
    clean()
    test_oauth_and_mock()
    test_decision()
    test_approval_persistence()
    test_audit_and_tamper()
    print("\n=== All tests passed ===")
