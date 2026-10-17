"""
CreatorSettle AI — Approval Layer
File-persisted. Execution must check status itself.
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
        "executed": False,
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

def get_status(txn_id: str) -> Optional[str]:
    data = _load()
    req = data.get(txn_id)
    if not req:
        return None
    # Check expiry on read
    if req["status"] == "PENDING":
        if datetime.fromisoformat(req["expires"].replace("Z", "")) < datetime.utcnow():
            req["status"] = "EXPIRED"
            _save(data)
    return req["status"]

def mark_executed(txn_id: str) -> bool:
    data = _load()
    req = data.get(txn_id)
    if not req or req.get("executed"):
        return False
    req["executed"] = True
    _save(data)
    return True

def is_executed(txn_id: str) -> bool:
    data = _load()
    return data.get(txn_id, {}).get("executed", False)
