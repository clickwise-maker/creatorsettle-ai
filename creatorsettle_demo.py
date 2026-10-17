"""
CreatorSettle AI — End-to-end Demo
Approval gate enforced before any API action.
"""

from creatorsettle_reader import get_access_token, fetch_failed_transactions, create_test_order
from creatorsettle_decision import decide_with_ai, LLMClient
from creatorsettle_approval import propose, decide as approval_decide
from creatorsettle_audit import append, verify

def main():
    print("=== CreatorSettle AI — End-to-End Demo ===\n")

    token = get_access_token()
    if token:
        print("[1] PayPal OAuth: SUCCESS")
    else:
        print("[1] PayPal OAuth: mock mode")

    llm = LLMClient()
    print(f"[AI] LLM: {'connected' if llm.api_key else 'rules only'}")

    txns = fetch_failed_transactions(token)
    print(f"\n[2] Detected {len(txns)} transactions (source: {txns[0].get('source') if txns else 'none'})\n")

    for txn in txns:
        action, conf, msg, exec_type = decide_with_ai(txn, llm)
        print(f"[3] {txn['id']} | {txn.get('decline_code')} → {action} ({exec_type})")
        print(f"    {msg}")

        # Approval first
        propose(txn["id"], action, msg)
        if action in ("ROUTE", "RETRY") and exec_type != "none":
            final = approval_decide(txn["id"], "APPROVE")
        else:
            final = approval_decide(txn["id"], "REJECT") if txn.get("decline_code") == "EXPIRED_CARD" else "PENDING"
        print(f"[4] Seller approval: {final}")

        # API action only after approval
        result = "no_action"
        if final == "APPROVED" and exec_type == "api" and token:
            order_id = create_test_order(token)
            result = f"api_called:{order_id or 'failed'}"
            print(f"[5] Executed after approval: {result}")
        elif exec_type == "instruction":
            result = "instruction_given"
            print(f"[5] Instruction given (no auto-execution)")
        else:
            print(f"[5] No execution")

        print(f"[6] Result recorded: {result}\n")

        append({
            "txn_id": txn["id"],
            "action": action,
            "execution_type": exec_type,
            "approval": final,
            "result": result,
            "message": msg,
        })

    print("[7] Audit chain valid:", verify())
    print("Open dashboard.html for the seller view.")
    print("=== Complete ===")

if __name__ == "__main__":
    main()
