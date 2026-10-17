"""
CreatorSettle AI — Execution
Server-side validation only. Does not trust client action/type alone.
"""

from typing import Optional, Dict
from creatorsettle_approval import get_status, is_executed, mark_executed, get_record
from creatorsettle_reader import get_transaction_status

def execute_action(txn_id: str, client_action: str = "", client_exec_type: str = "", access_token: Optional[str] = None) -> Dict:
    record = get_record(txn_id)
    if not record:
        return {"executed": False, "reason": "blocked: no approval record", "verification": None}

    status = get_status(txn_id)
    if status != "APPROVED":
        return {
            "executed": False,
            "reason": f"blocked: approval status is {status or 'missing'}",
            "verification": None,
        }

    if is_executed(txn_id):
        return {
            "executed": False,
            "reason": "blocked: already executed (duplicate protection)",
            "verification": None,
        }

    # Use stored action, not client-supplied
    stored_action = record.get("action", "HOLD")
    # Always instruction for this prototype
    exec_type = "instruction"

    if not mark_executed(txn_id):
        return {"executed": False, "reason": "blocked: failed to mark executed", "verification": None}

    verified_status = None
    if access_token:
        verified_status = get_transaction_status(access_token, txn_id)

    return {
        "executed": True,
        "reason": "instruction_given (no payment recovery performed)",
        "stored_action": stored_action,
        "verification": verified_status,
    }
