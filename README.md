# CreatorSettle AI

Honest settlement-recovery prototype. The dashboard runs locally at `127.0.0.1`.

## Supported recovery action

The integrated recovery action is **PayPal subscription outstanding-balance capture**. It is separate from the one-time transaction dashboard.

1. Start the dashboard and enter an existing PayPal subscription ID, amount, and currency.
2. Create an approval request and review the exact subscription and amount.
3. Explicitly approve the request.
4. Click **Submit capture to PayPal** separately to make the API request.
5. Check the returned state and verify the payment in PayPal if the request is pending or the result is uncertain.

The backend calls:

`POST /v1/billing/subscriptions/{id}/capture`

with `capture_type: OUTSTANDING_BALANCE`.

- Defaults to PayPal Sandbox: `https://api-m.sandbox.paypal.com`.
- Credentials are read from `PAYPAL_CLIENT_ID` and `PAYPAL_SECRET`.
- `PAYPAL_BASE_URL` can override the API base URL. Production credentials/base URL can move real money; test in Sandbox first.
- Inputs are validated server-side.
- Duplicate execution of the same persisted approval is blocked.
- HTTP 202 is labelled `REQUEST_ACCEPTED`, not completed.
- A confirmed state requires an HTTP 200/201 response whose JSON status is `COMPLETED`.
- If the network result is uncertain, the request is intentionally not auto-retried. Check PayPal before creating another request.
- Approval records are stored locally in `approvals.json`. Protect this file and do not commit credentials or live customer data.

**Important limitation:** this is not recovery of arbitrary failed one-time payments. The main transaction dashboard continues to provide instructions for one-time failures. Creating a new order is a new payment, not recovery of the old one.

## Setup

Python 3.10+ recommended.

```bash
pip install -r requirements.txt
python backend.py
```

Open http://127.0.0.1:5000.

Set credentials in a local `.env` file (do not commit it):

```dotenv
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_SECRET=your_sandbox_secret
# Optional; Sandbox is the default:
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
```

## Tests

All automated recovery tests mock PayPal HTTP calls; they do **not** make a real capture.

```bash
python test_recovery.py
python test_subscription_capture_flow.py
python test_creatorsettle.py
```

A passing mock suite verifies application logic only. It does not prove that PayPal credentials, subscription eligibility, or a live/Sandbox capture will work. Do a controlled Sandbox check with a test subscription before production use.
