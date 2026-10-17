"""
CreatorSettle AI — Execution
Server-side approval checks. One-time transaction actions remain instruction-only.
"""
from typing import Optional, Dict
from creatorsettle_approval import get_status, is_executed, mark_executed, get_record
from creatorsettle_reader import get_transaction_status
from creatorsettle_recovery import capture_outstanding_balance


def execute_action(txn_id: str, client_action: str = "", client_exec_type: str = "",
                   access_token: Optional[str] = None) -> Dict:
    record = get_record(txn_id)
    if not record:
        return {"executed": False, "state": "BLOCKED", "reason": "blocked: no approval record", "verification": None}

    status = get_status(txn_id)
    if status != "APPROVED":
        return {"executed": False, "state": "BLOCKED",
                "reason": f"blocked: approval status is {status or 'missing'}", "verification": None}

    if is_executed(txn_id):
        return {"executed": False, "state": "BLOCKED",
                "reason": "blocked: already executed (duplicate protection)", "verification": None}

    # Trust only the server-side approved record, never client-supplied action/type.
    stored_action = record.get("action", "HOLD")
    metadata = record.get("metadata") or {}

    # Claim the approval before any external money movement. If the network result is
    # ambiguous, this intentionally blocks automatic retries to avoid duplicate captures.
    if not mark_executed(txn_id):
        return {"executed": False, "state": "BLOCKED",
                "reason": "blocked: failed to claim execution or already claimed", "verification": None}

    if stored_action == "CAPTURE_SUBSCRIPTION_BALANCE":
        sub_id = metadata.get("subscription_id")
        amount = metadata.get("amount")
        currency = metadata.get("currency", "USD")
        if not sub_id or not amount:
            return {"executed": True, "state": "FAILED",
                    "reason": "approved recovery request missing required metadata",
                    "stored_action": stored_action, "verification": None}
        result = capture_outstanding_balance(sub_id, amount, currency, note=f"CreatorSettle approval {txn_id}")
        return {
            "executed": True,
            "state": result.get("state", "FAILED"),
            "reason": result.get("reason", "recovery_result_unavailable"),
            "stored_action": stored_action,
            "recovery": result,
            "verification": None,
        }

    # Existing one-time transaction actions are instructions only; no arbitrary
    # failed payment is automatically re-captured or retried.
    verified_status = get_transaction_status(access_token, txn_id) if access_token else None
    return {
        "executed": True,
        "state": "INSTRUCTION_ONLY",
        "reason": "instruction_given (no payment recovery performed)",
        "stored_action": stored_action,
        "verification": verified_status,
    }
