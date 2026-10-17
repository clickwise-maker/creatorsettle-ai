# CreatorSettle AI

**Honest end-to-end settlement recovery prototype.**

Seller connects PayPal → detect failure → agent diagnoses → seller approves → safe action (API or instruction) → verify status → dashboard + audit.

Where PayPal does not support automatic recovery, the agent gives a clear instruction instead of claiming success.

## Workflow

1. OAuth + transaction history (PayPal Sandbox)
2. Detect failure (status, amount, retry count)
3. Decide: RETRY / ROUTE / HOLD / ESCALATE
4. Seller approval (file-persisted)
5. Execute only what the API allows (or return instruction)
6. Verify result
7. Dashboard + hash-chain audit

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Add PayPal Sandbox credentials (and optional LLM key)
python creatorsettle_demo.py
# Open dashboard.html in a browser
```

## Honesty Notes

- Recovery execution is real only for supported Orders API calls (e.g. create order).
- Alternate funding source and card update are **instructions**, not automatic actions.
- Approval is file-persisted. Audit is a hash-chain integrity check.

## License

MIT
