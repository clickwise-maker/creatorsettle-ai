"""
CreatorSettle AI — End-to-end Demo
Clearly shows mock vs real and simulated approval.
"""

from creatorsettle_reader import get_access_token, fetch_failed_transactions, create_test_order
from creatorsettle_decision import decide
from creatorsettle_approval import propose, decide as approval_decide
from creatorsettle_audit import append, verify

def main():
    print("=== CreatorSettle AI Demo ===\n")

    token = get_access_token()
    if token:
        print("[Mode] Real PayPal Sandbox OAuth: SUCCESS")
        # Demonstrate one real recovery-style action
        order_id = create_test_order(token)
        if order_id:
            print(f"[Real Action] Created test order: {order_id}")
        else:
            print("[Real Action] Test order creation failed (permissions or sandbox limit).")
    else:
        print("[Mode] Mock mode (no valid PayPal credentials)")

    txns = fetch_failed_transactions(token)
    source = txns[0].get("source", "unknown") if txns else "none"
    print(f"\nProcessing {len(txns)} transactions (source: {source})\n")

    for txn in txns:
        action, confidence, message = decide(txn)
        print(f"TXN {txn['id']} | {txn.get('decline_code') or 'NONE'} → {action} ({confidence:.0%})")
        print(f"  → {message}")

        status = propose(txn["id"], action, message)
        print(f"  Approval: {status} (in-memory, simulated)")

        # Simulated creator response
        if action == "ROUTE":
            final = approval_decide(txn["id"], "APPROVE")
        elif action == "ALERT" and txn.get("decline_code") == "EXPIRED_CARD":
            final = approval_decide(txn["id"], "REJECT")
        else:
            final = "PENDING"
        print(f"  Simulated final: {final}\n")

        append({
            "txn_id": txn["id"],
            "action": action,
            "confidence": confidence,
            "approval": final,
            "message": message,
            "source": source,
        })

    print("Audit chain valid:", verify())
    print("Note: Approval is in-memory. Audit is a hash-chain integrity check, not a full tamper-proof system.")
    print("\n=== Demo complete ===")

if __name__ == "__main__":
    main()
