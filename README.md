# CreatorSettle AI

Honest settlement recovery prototype.

## Real supported recovery

**Subscription outstanding balance capture**

```bash
python -c "
from creatorsettle_recovery import capture_outstanding_balance
print(capture_outstanding_balance('I-XXXXXXXX', '20.00'))
"
```

This calls the real PayPal endpoint:
`POST /v1/billing/subscriptions/{id}/capture` with `capture_type: OUTSTANDING_BALANCE`.

- Success only if the API returns 200/201/202.
- No credentials or API error → `success: false`.
- This is **not** recovery of an arbitrary failed one-time payment.

## What is not real recovery

- One-time failed transactions from Transaction Search cannot be directly retried via a public “retry this capture” API.
- Creating a new order is a new payment, not recovery of a previous failure.
- The main agent currently returns **instructions** for one-time failures.

## Local dashboard

```bash
pip install -r requirements.txt
python backend.py
# http://127.0.0.1:5000
```

Approvals are file-persisted. Reject never triggers execution.
