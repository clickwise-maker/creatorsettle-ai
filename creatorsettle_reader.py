"""
CreatorSettle AI — Reader Module
Fetches failed/pending settlements from PayPal Sandbox.
"""

import os
import json
from typing import List, Dict

# Placeholder — replace with real PayPal SDK calls in production
def get_access_token() -> str:
    client_id = os.getenv("PAYPAL_CLIENT_ID", "sandbox_client_id")
    secret = os.getenv("PAYPAL_SECRET", "sandbox_secret")
    # In real code: POST to https://api-m.sandbox.paypal.com/v1/oauth2/token
    return "sandbox_access_token_placeholder"

def fetch_failed_transactions(access_token: str) -> List[Dict]:
    """Return mock failed transactions for demo. Replace with real API call."""
    return [
        {"id": "TXN-001", "amount": 120.50, "currency": "USD", "decline_code": "INSUFFICIENT_FUNDS", "retry_count": 1},
        {"id": "TXN-002", "amount": 89.00, "currency": "USD", "decline_code": "EXPIRED_CARD", "retry_count": 0},
        {"id": "TXN-003", "amount": 250.00, "currency": "USD", "decline_code": "FRAUD_FILTER", "retry_count": 2},
        {"id": "TXN-004", "amount": 45.00, "currency": "USD", "decline_code": "INSUFFICIENT_FUNDS", "retry_count": 2},
        {"id": "TXN-005", "amount": 15.00, "currency": "USD", "decline_code": None, "retry_count": 0},
    ]

def get_account_overview(access_token: str) -> Dict:
    return {"balance": 1840.75, "pending": 3, "failed_last_7d": 5}
