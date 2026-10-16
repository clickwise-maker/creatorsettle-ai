"""
CreatorSettle AI — Approval Layer
Creator one-tap approve / reject before any action is executed.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional

class ApprovalRequest:
    def __init__(self, txn_id: str, action: str, message: str, expires_minutes: int = 30):
        self.txn_id = txn_id
        self.action = action
        self.message = message
        self.created = datetime.utcnow()
        self.expires = self.created + timedelta(minutes=expires_minutes)
        self.status = "PENDING"  # PENDING / APPROVED / REJECTED / EXPIRED

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires

    def approve(self) -> bool:
        if self.status != "PENDING" or self.is_expired():
            return False
        self.status = "APPROVED"
        return True

    def reject(self) -> bool:
        if self.status != "PENDING":
            return False
        self.status = "REJECTED"
        return True

# In-memory store for demo
_requests: Dict[str, ApprovalRequest] = {}

def propose(txn_id: str, action: str, message: str) -> str:
    req = ApprovalRequest(txn_id, action, message)
    _requests[txn_id] = req
    return req.status

def decide(txn_id: str, decision: str) -> Optional[str]:
    req = _requests.get(txn_id)
    if not req:
        return None
    if decision.upper() == "APPROVE":
        return "APPROVED" if req.approve() else req.status
    if decision.upper() == "REJECT":
        return "REJECTED" if req.reject() else req.status
    return req.status
