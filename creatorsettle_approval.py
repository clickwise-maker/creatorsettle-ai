"""
CreatorSettle AI — Approval Layer
File-persisted approval requests (survives process restart).
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

APPROVAL_FILE = Path("approvals.json")

def _load() -> Dict:
    if APPROVAL_FILE.exists():
        try:
            return json.loads(APPROVAL_FILE.read_text())
        except Exception:
            return {}
    return {}

def _save(data: Dict):
    APPROVAL_FILE.write_text(json.dumps(data, indent=2))

def propose(txn_id: str, action: str, message: str, expires_minutes: int = 30) -> str:
    data = _load()
    data[txn_id] = {
        "action": action,
        "message": message,
        "status": "PENDING",
        "created": datetime.utcnow().isoformat() + "Z",
        "expires": (datetime.utcnow() + timedelta(minutes=expires_minutes)).isoformat() + "Z",
    }
    _save(data)
    return "PENDING"

def decide(txn_id: str, decision: str) -> Optional[str]:
    data = _load()
    req = data.get(txn_id)
    if not req:
        return None
    if req["status"] != "PENDING":
        return req["status"]
    # Check expiry
    if datetime.fromisoformat(req["expires"].replace("Z", "")) < datetime.utcnow():
        req["status"] = "EXPIRED"
        _save(data)
        return "EXPIRED"
    if decision.upper() == "APPROVE":
        req["status"] = "APPROVED"
    elif decision.upper() == "REJECT":
        req["status"] = "REJECTED"
    _save(data)
    return req["status"]
