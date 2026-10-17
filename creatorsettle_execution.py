"""
CreatorSettle AI — Execution
Verifies approval itself. Never treats unrelated create-order as recovery.
"""

from typing import Optional, Dict
from creatorsettle_approval import get_status, is_executed, mark_executed
from creatorsettle_reader import get_transaction_status

def execute_action(txn_id: str, action: str, exec_type: str, access_token: Optional[str] = None) -> Dict:
    """
    Returns result dict. Checks approval status itself.
    Blocks on pending / rejected / expired / already executed.
    """
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

    # No supported recovery API for existing failed transaction.
    # Therefore we never call create_test_order here.
    if exec_type != "instruction":
        return {
            "executed": False,
            "reason": f"no supported execution for type={exec_type}",
            "verification": None,
        }

    # Instruction path: mark as "executed" meaning instruction delivered
    mark_executed(txn_id)

    # Attempt verification (usually unavailable)
    verified_status = None
    if access_token:
        verified_status = get_transaction_status(access_token, txn_id)

    return {
        "executed": True,
        "reason": "instruction_given (no API recovery performed)",
        "verification": verified_status,
    }
