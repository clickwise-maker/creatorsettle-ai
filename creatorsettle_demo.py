"""
CreatorSettle AI — Demo
No automatic approval. Execution verifies approval itself.
"""

from creatorsettle_reader import get_access_token, fetch_failed_transactions
from creatorsettle_decision import decide_with_ai, LLMClient
from creatorsettle_approval import propose, decide as approval_decide
from creatorsettle_execution import execute_action
from creatorsettle_audit import append, verify

def main():
    print("=== CreatorSettle AI Demo ===\n")

    token = get_access_token()
    print(f"[1] OAuth: {'SUCCESS' if token else 'mock mode'}")

    llm = LLMClient()
    print(f"[AI] {'connected' if llm.api_key else 'rules only'}")

    txns = fetch_failed_transactions(token)
    print(f"[2] Transactions: {len(txns)} (source: {txns[0].get('source') if txns else 'none'})\n")

    for txn in txns:
        action, conf, msg, exec_type = decide_with_ai(txn, llm)
        print(f"[3] {txn['id']} | {txn.get('decline_code')} → {action} ({exec_type})")
        print(f"    {msg}")

        propose(txn["id"], action, msg)
        print(f"[4] Approval proposed: PENDING")
        print(f"    (In real use, seller must explicitly approve via dashboard or API)")

        # Do NOT auto-approve. Show what happens without approval.
        result = execute_action(txn["id"], action, exec_type, token)
        print(f"[5] Execution result: {result['reason']}")
        print(f"    Verification: {result['verification']}\n")

        append({
            "txn_id": txn["id"],
            "action": action,
            "execution_type": exec_type,
            "result": result["reason"],
            "verification": result["verification"],
        })

    print("[7] Audit valid:", verify())
    print("Note: No recovery was executed. Instructions only.")
    print("=== Done ===")

if __name__ == "__main__":
    main()
