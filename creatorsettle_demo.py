"""
CreatorSettle AI — End-to-end Demo
Runs a full cycle on mock failed settlements and verifies the audit chain.
"""

from creatorsettle_reader import get_access_token, fetch_failed_transactions
from creatorsettle_decision import decide
from creatorsettle_approval import propose, decide as approval_decide
from creatorsettle_audit import append, verify

def main():
    print("=== CreatorSettle AI Demo ===\n")

    token = get_access_token()
    if not token:
        print("WARNING: No PayPal credentials found. Using mock mode only.")
        print("Set PAYPAL_CLIENT_ID and PAYPAL_SECRET in .env for real OAuth.\n")
        token = "mock_token"

    txns = fetch_failed_transactions(token)
    print(f"Processing {len(txns)} transactions...\n")

    for txn in txns:
        action, confidence, message = decide(txn)
        print(f"TXN {txn['id']} | {txn.get('decline_code') or 'NONE'} → {action} ({confidence:.0%})")
        print(f"  → {message}")

        status = propose(txn["id"], action, message)
        print(f"  Approval request: {status}")

        # Simulate creator response for demo
        if action == "ROUTE":
            final = approval_decide(txn["id"], "APPROVE")
        elif action == "ALERT" and txn.get("decline_code") == "EXPIRED_CARD":
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
    print("\n=== Demo complete ===")

if __name__ == "__main__":
    main()
