"""
CreatorSettle AI — End-to-end Demo
"""

from creatorsettle_reader import get_access_token, fetch_failed_transactions, create_test_order
from creatorsettle_decision import decide_with_ai, LLMClient
from creatorsettle_approval import propose, decide as approval_decide
from creatorsettle_audit import append, verify

def main():
    print("=== CreatorSettle AI Demo ===\n")

    token = get_access_token()
    if token:
        print("[Mode] Real PayPal Sandbox OAuth: SUCCESS")
        order_id = create_test_order(token)
        print(f"[Real Action] Test order: {order_id or 'not created'}")
    else:
        print("[Mode] Mock mode (no PayPal credentials)")

    llm = LLMClient()
    if llm.api_key:
        print("[AI] LLM key detected — using real model for messages")
    else:
        print("[AI] No LLM key — using deterministic decisions")

    txns = fetch_failed_transactions(token)
    source = txns[0].get("source", "unknown") if txns else "none"
    print(f"\nProcessing {len(txns)} transactions (source: {source})\n")

    for txn in txns:
        action, confidence, message = decide_with_ai(txn, llm)
        print(f"TXN {txn['id']} | {txn.get('decline_code') or 'NONE'} → {action} ({confidence:.0%})")
        print(f"  → {message}")

        propose(txn["id"], action, message)
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
    print("Note: Recovery execution is simulated. Approval is file-persisted.")
    print("\n=== Demo complete ===")

if __name__ == "__main__":
    main()
