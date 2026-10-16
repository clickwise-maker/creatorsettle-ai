"""
CreatorSettle AI — End-to-end Demo
Honest prototype: real OAuth + optional real order, simulated recovery, persisted approval, hash-chain audit.
"""

from creatorsettle_reader import get_access_token, fetch_failed_transactions, create_test_order
from creatorsettle_decision import decide_with_ai
from creatorsettle_approval import propose, decide as approval_decide
from creatorsettle_audit import append, verify

def main():
    print("=== CreatorSettle AI Demo ===\n")

    token = get_access_token()
    if token:
        print("[Mode] Real PayPal Sandbox OAuth: SUCCESS")
        order_id = create_test_order(token)
        print(f"[Real Action] Test order: {order_id or 'not created (sandbox limit or scope)'}")
    else:
        print("[Mode] Mock mode (no valid credentials)")

    txns = fetch_failed_transactions(token)
    source = txns[0].get("source", "unknown") if txns else "none"
    print(f"\nProcessing {len(txns)} transactions (source: {source})\n")

    for txn in txns:
        action, confidence, message = decide_with_ai(txn)
        print(f"TXN {txn['id']} | {txn.get('decline_code') or 'NONE'} → {action} ({confidence:.0%})")
        print(f"  → {message}")

        propose(txn["id"], action, message)
        # Simulated creator response for demo
        if action == "ROUTE":
            final = approval_decide(txn["id"], "APPROVE")
        elif txn.get("decline_code") == "EXPIRED_CARD":
            final = approval_decide(txn["id"], "REJECT")
        else:
            final = "PENDING"
        print(f"  Approval (persisted): {final}\n")

        append({
            "txn_id": txn["id"],
            "action": action,
            "confidence": confidence,
            "approval": final,
            "message": message,
            "source": source,
        })

    print("Audit chain valid:", verify())
    print("Note: Recovery execution beyond test order is simulated.")
    print("Approval is file-persisted. Audit is a hash-chain integrity check.")
    print("\n=== Demo complete ===")

if __name__ == "__main__":
    main()
