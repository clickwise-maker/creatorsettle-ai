"""
CreatorSettle AI — Approval Layer
Atomic-style transitions. propose() does not reset existing decided or executed records.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import threading

APPROVAL_FILE = Path("approvals.json")
_lock = threading.Lock()

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
    with _lock:
        data = _load()
        existing = data.get(txn_id)
        if existing:
            status = existing.get("status")
            if status in ("APPROVED", "REJECTED", "EXPIRED") or existing.get("executed"):
                return status or "EXECUTED"
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
    with _lock:
        data = _load()
        req = data.get(txn_id)
        if not req:
            return None
        if req.get("executed"):
            return "EXECUTED"
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
        else:
            return req["status"]
        _save(data)
        return req["status"]

def get_status(txn_id: str) -> Optional[str]:
    with _lock:
        data = _load()
        req = data.get(txn_id)
        if not req:
            return None
        if req.get("executed"):
            return "EXECUTED"
        if req["status"] == "PENDING":
            if datetime.fromisoformat(req["expires"].replace("Z", "")) < datetime.utcnow():
                req["status"] = "EXPIRED"
                _save(data)
        return req["status"]

def mark_executed(txn_id: str) -> bool:
    with _lock:
        data = _load()
        req = data.get(txn_id)
        if not req or req.get("executed") or req.get("status") != "APPROVED":
            return False
        req["executed"] = True
        req["status"] = "EXECUTED"
        _save(data)
        return True

def is_executed(txn_id: str) -> bool:
    data = _load()
    return data.get(txn_id, {}).get("executed", False)

def get_record(txn_id: str) -> Optional[Dict]:
    return _load().get(txn_id)
