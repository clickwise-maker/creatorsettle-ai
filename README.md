# CreatorSettle AI

Honest settlement recovery prototype.

## What is real

- PayPal Sandbox OAuth (when credentials present)
- Transaction Search fetch (when permitted)
- File-persisted approval
- Hash-chain audit with tamper detection
- Decision engine (rules + optional LLM message)

## What is not real / simulated

- **Recovery of an existing failed transaction** — PayPal Sandbox scope used here does not support retrying a specific failed capture. Therefore the agent returns an **instruction**, not an API recovery.
- Creating a new $10 order is **not** treated as recovery of a previous failure.
- Status re-verification after action is limited (Transaction Search does not support easy single-ID lookup in this prototype).
- Dashboard buttons currently show the intended flow; full live backend is out of scope for this submission.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env
python test_creatorsettle.py
python creatorsettle_demo.py
```

## Honesty

No claim is made that a failed payment was automatically recovered. The agent diagnoses, asks for approval, and either delivers a clear instruction or blocks the action.
