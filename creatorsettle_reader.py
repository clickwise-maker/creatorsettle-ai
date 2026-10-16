"""
CreatorSettle AI — Reader Module
Fetches failed/pending settlements from PayPal Sandbox.
"""

import os
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta

BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

def get_access_token() -> Optional[str]:
    """Get OAuth2 access token from PayPal Sandbox."""
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    secret = os.getenv("PAYPAL_SECRET")

    if not client_id or not secret:
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
    Attempt real Transaction Search, fall back to high-quality mock data.
    Real endpoint: GET /v1/reporting/transactions (requires Transactions Search scope).
    """
    if access_token and access_token != "mock_token":
        try:
            end = datetime.utcnow()
            start = end - timedelta(days=30)
            params = {
                "start_date": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "end_date": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "fields": "transaction_info",
                "page_size": 20,
            }
            resp = requests.get(
                f"{BASE_URL}/v1/reporting/transactions",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                params=params,
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Parse real transactions if available
                real = []
                for item in data.get("transaction_details", []):
                    info = item.get("transaction_info", {})
                    real.append({
                        "id": info.get("transaction_id", "UNKNOWN"),
                        "amount": float(info.get("transaction_amount", {}).get("value", 0)),
                        "currency": info.get("transaction_amount", {}).get("currency_code", "USD"),
                        "decline_code": info.get("transaction_status"),
                        "retry_count": 0,
                    })
                if real:
                    return real
        except Exception as e:
            print(f"Real transaction fetch failed, using mock: {e}")

    # High-quality mock for reliable demo
    return [
        {"id": "TXN-001", "amount": 120.50, "currency": "USD", "decline_code": "INSUFFICIENT_FUNDS", "retry_count": 1},
        {"id": "TXN-002", "amount": 89.00, "currency": "USD", "decline_code": "EXPIRED_CARD", "retry_count": 0},
        {"id": "TXN-003", "amount": 250.00, "currency": "USD", "decline_code": "FRAUD_FILTER", "retry_count": 2},
        {"id": "TXN-004", "amount": 45.00, "currency": "USD", "decline_code": "INSUFFICIENT_FUNDS", "retry_count": 2},
        {"id": "TXN-005", "amount": 15.00, "currency": "USD", "decline_code": None, "retry_count": 0},
    ]

def get_account_overview(access_token: str) -> Dict:
    return {"balance": 1840.75, "pending": 3, "failed_last_7d": 5}

if __name__ == "__main__":
    token = get_access_token()
    if token:
        print("Access token obtained successfully.")
        txns = fetch_failed_transactions(token)
        print(f"Fetched {len(txns)} transactions.")
    else:
        print("No credentials. Running in mock mode.")
        print(fetch_failed_transactions("mock_token"))
