"""
CreatorSettle AI — Reader Module
Fetches transactions from PayPal Sandbox with clear mock fallback.
"""

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

def get_access_token() -> Optional[str]:
    """Get OAuth2 access token. Returns None on failure."""
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
        print(f"[OAuth] Failed: {e}")
        return None

def fetch_failed_transactions(access_token: str) -> List[Dict]:
    """
    Try real Transaction Search. On failure or empty result, return clearly labeled mock data.
    """
    if not access_token:
        return _mock_transactions()

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
            real = []
            for item in data.get("transaction_details", []):
                info = item.get("transaction_info", {})
                status = info.get("transaction_status", "").upper()
                # Map real status to our decline-like codes for demo
                decline = None
                if status in ("DENIED", "FAILED", "PENDING"):
                    decline = status
                real.append({
                    "id": info.get("transaction_id", "UNKNOWN"),
                    "amount": float(info.get("transaction_amount", {}).get("value", 0) or 0),
                    "currency": info.get("transaction_amount", {}).get("currency_code", "USD"),
                    "decline_code": decline,
                    "retry_count": 0,
                    "source": "real",
                })
            if real:
                print(f"[Reader] Got {len(real)} real transactions.")
                return real
        print(f"[Reader] Real API returned {resp.status_code}. Using mock.")
    except Exception as e:
        print(f"[Reader] Real fetch error: {e}. Using mock.")

    return _mock_transactions()

def _mock_transactions() -> List[Dict]:
    """Clearly labeled mock data for demo reliability."""
    return [
        {"id": "MOCK-001", "amount": 120.50, "currency": "USD", "decline_code": "INSUFFICIENT_FUNDS", "retry_count": 1, "source": "mock"},
        {"id": "MOCK-002", "amount": 89.00, "currency": "USD", "decline_code": "EXPIRED_CARD", "retry_count": 0, "source": "mock"},
        {"id": "MOCK-003", "amount": 250.00, "currency": "USD", "decline_code": "FRAUD_FILTER", "retry_count": 2, "source": "mock"},
        {"id": "MOCK-004", "amount": 45.00, "currency": "USD", "decline_code": "INSUFFICIENT_FUNDS", "retry_count": 2, "source": "mock"},
        {"id": "MOCK-005", "amount": 15.00, "currency": "USD", "decline_code": None, "retry_count": 0, "source": "mock"},
    ]

def create_test_order(access_token: str) -> Optional[str]:
    """Real Sandbox action: create a test order (supported recovery-style call)."""
    if not access_token:
        return None
    try:
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {"currency_code": "USD", "value": "10.00"}
            }]
        }
        resp = requests.post(
            f"{BASE_URL}/v2/checkout/orders",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=15,
        )
        if resp.status_code in (200, 201):
            return resp.json().get("id")
    except Exception as e:
        print(f"[Order] Failed to create test order: {e}")
    return None

if __name__ == "__main__":
    print("=== Reader Test ===")
    token = get_access_token()
    if token:
        print("OAuth: SUCCESS")
        txns = fetch_failed_transactions(token)
        print(f"Transactions: {len(txns)} (source: {txns[0].get('source', 'unknown')})")
        order_id = create_test_order(token)
        print(f"Test order created: {order_id or 'FAILED'}")
    else:
        print("OAuth: FAILED (no credentials or error)")
        print("Mock transactions:", fetch_failed_transactions(None))
