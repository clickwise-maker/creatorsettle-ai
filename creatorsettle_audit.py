"""
CreatorSettle AI — Audit Logger
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict

AUDIT_FILE = Path("audit.jsonl")

def _hash(record: Dict) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()

def append(record: Dict) -> Dict:
    record["timestamp"] = datetime.utcnow().isoformat() + "Z"
    if AUDIT_FILE.exists():
        lines = AUDIT_FILE.read_text().strip().splitlines()
        prev = json.loads(lines[-1])["hash"] if lines else "GENESIS"
    else:
        prev = "GENESIS"
    record["prev_hash"] = prev
    record["hash"] = _hash(record)
    with AUDIT_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return record

def verify() -> bool:
    if not AUDIT_FILE.exists():
        return True
    lines = [l for l in AUDIT_FILE.read_text().strip().splitlines() if l]
    prev = "GENESIS"
    for line in lines:
        rec = json.loads(line)
        expected = _hash({k: v for k, v in rec.items() if k != "hash"})
        if rec["prev_hash"] != prev or rec["hash"] != expected:
            return False
        prev = rec["hash"]
    return True

def test_tamper() -> bool:
    """Temporarily tamper and confirm detection. Restores original file."""
    if not AUDIT_FILE.exists():
        append({"test": "genesis"})
    original = AUDIT_FILE.read_text()
    lines = original.strip().splitlines()
    last = json.loads(lines[-1])
    last["action"] = "TAMPERED"
    lines[-1] = json.dumps(last)
    AUDIT_FILE.write_text("\n".join(lines) + "\n")
    detected = not verify()
    # Restore
    AUDIT_FILE.write_text(original)
    return detected
