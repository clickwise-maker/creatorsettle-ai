"""
CreatorSettle AI — Reader Module
Fetches failed/pending settlements from PayPal Sandbox.
"""

import os
import json
import requests
from typing import List, Dict, Optional

BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

def get_access_token() -> Optional[str]:
    """Get OAuth2 access token from PayPal Sandbox."""
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    secret = os.getenv("PAYPAL_SECRET")

    if not client_id or not secret:
        print("ERROR: PAYPAL_CLIENT_ID and PAYPAL_SECRET must be set in environment.")
        return None

    try:
        response = requests.post(
            f"{BASE_URL}/v1/oauth2/token",
            auth=(client_id, secret),
            headers={"Accept": "application/json", "Accept-Language": "en_US"},
            data={"grant_type": "client_credentials"},
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        print(f"Failed to get access token: {e}")
        return None

def fetch_failed_transactions(access_token: str) -> List[Dict]:
    """
    Fetch recent transactions and filter for failed/declined ones.
    Note: PayPal Reporting API or Transaction Search is needed for full history.
    For demo, we return structured mock data that matches real decline codes.
    Replace the body with real API calls once you have Transaction Search enabled.
    """
    if not access_token:
        return []

    # TODO: Replace with real call to PayPal Transaction Search or Reporting API
    # Example endpoint (requires approval): /v1/reporting/transactions
    # For now, return realistic mock data so the rest of the pipeline works.
    return [
        {"id": "TXN-001", "amount": 120.50, "currency": "USD", "decline_code": "INSUFFICIENT_FUNDS", "retry_count": 1},
        {"id": "TXN-002", "amount": 89.00, "currency": "USD", "decline_code": "EXPIRED_CARD", "retry_count": 0},
        {"id": "TXN-003", "amount": 250.00, "currency": "USD", "decline_code": "FRAUD_FILTER", "retry_count": 2},
        {"id": "TXN-004", "amount": 45.00, "currency": "USD", "decline_code": "INSUFFICIENT_FUNDS", "retry_count": 2},
        {"id": "TXN-005", "amount": 15.00, "currency": "USD", "decline_code": None, "retry_count": 0},
    ]

def get_account_overview(access_token: str) -> Dict:
    """Get basic account overview (mock for now)."""
    return {"balance": 1840.75, "pending": 3, "failed_last_7d": 5}

if __name__ == "__main__":
    token = get_access_token()
    if token:
        print("Access token obtained successfully.")
        print("Sample failed transactions:", fetch_failed_transactions(token))
    else:
        print("Could not obtain access token. Check credentials.")
