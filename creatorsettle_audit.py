"""
CreatorSettle AI — Tamper-proof Audit Logger
Hash-chain of every decision so judges can verify integrity.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict

AUDIT_FILE = Path("demo_audit.jsonl")

def _hash(record: Dict) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()

def append(record: Dict) -> Dict:
    record["timestamp"] = datetime.utcnow().isoformat() + "Z"
    if AUDIT_FILE.exists():
        last_line = AUDIT_FILE.read_text().strip().splitlines()[-1]
        prev = json.loads(last_line)["hash"]
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
    lines = AUDIT_FILE.read_text().strip().splitlines()
    prev = "GENESIS"
    for line in lines:
        rec = json.loads(line)
        expected = _hash({k: v for k, v in rec.items() if k != "hash"})
        if rec["prev_hash"] != prev or rec["hash"] != expected:
            return False
        prev = rec["hash"]
    return True
