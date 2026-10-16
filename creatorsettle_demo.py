"""
CreatorSettle AI — End-to-end Demo
Runs a full cycle on mock failed settlements.
"""

from creatorsettle_reader import fetch_failed_transactions, get_access_token
from creatorsettle_decision import decide
from creatorsettle_approval import propose, decide as approval_decide
from creatorsettle_audit import append, verify

def main():
    print("=== CreatorSettle AI Demo ===\n")
    token = get_access_token()
    txns = fetch_failed_transactions(token)

    for txn in txns:
        action, confidence, message = decide(txn)
        print(f"TXN {txn['id']} | {txn['decline_code'] or 'NONE'} → {action} ({confidence:.0%})")
        print(f"  → {message}")

        status = propose(txn["id"], action, message)
        print(f"  Approval request: {status}")

        # Simulate creator response for demo
        if action == "ROUTE":
            final = approval_decide(txn["id"], "APPROVE")
        elif action == "ALERT" and txn["decline_code"] == "EXPIRED_CARD":
            final = approval_decide(txn["id"], "REJECT")
        else:
            final = "PENDING"
        print(f"  Final: {final}\n")

        append({
            "txn_id": txn["id"],
            "action": action,
            "confidence": confidence,
            "approval": final,
            "message": message
        })

    print("Audit chain valid:", verify())

if __name__ == "__main__":
    main()
