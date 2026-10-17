# CreatorSettle AI

Honest settlement recovery prototype.

## What is real

- PayPal Sandbox OAuth (when credentials present)
- Transaction Search fetch of failed-like statuses (when permitted)
- File-persisted approval with server-side validation
- Hash-chain audit with tamper detection
- Decision engine (rules + optional LLM message)
- Local dashboard connected to Flask backend (binds to 127.0.0.1)

## What is simulated / not recovery

- **Issuing an instruction is not payment recovery.** The agent does not retry or reroute an existing failed PayPal transaction.
- Creating a new order is not used as recovery.
- Status re-verification after an action returns `None` (single-ID lookup not supported in this scope).
- No authentication or CSRF protection. Dashboard is local-only by default.

## What is unverified

- Concurrent multi-process safety beyond a simple thread lock.
- Full end-to-end recovery of a real failed capture.

## Quick start

```bash
pip install -r requirements.txt
python test_creatorsettle.py
python backend.py
# open http://127.0.0.1:5000
```
