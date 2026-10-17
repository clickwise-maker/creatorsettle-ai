"""
CreatorSettle AI — Reader Module
Honest transaction fetch. No invented decline reasons.
"""

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

def get_access_token() -> Optional[str]:
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

def fetch_failed_transactions(access_token: Optional[str]) -> List[Dict]:
    """
    Fetch real transactions. Only include failed/denied/declined.
    Do not invent decline reasons. Fall back to clearly labeled mock.
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
                status = (info.get("transaction_status") or "").upper()
                # Only failed-like statuses. Do not invent reason.
                if status in ("DENIED", "FAILED", "DECLINED", "VOIDED"):
                    real.append({
                        "id": info.get("transaction_id", "UNKNOWN"),
                        "amount": float(info.get("transaction_amount", {}).get("value", 0) or 0),
                        "currency": info.get("transaction_amount", {}).get("currency_code", "USD"),
                        "status": status,
                        "decline_code": status,  # raw status only
                        "retry_count": 0,
                        "source": "real",
                    })
            if real:
                print(f"[Reader] Got {len(real)} real failed transactions.")
                return real
            print("[Reader] No failed transactions in real data. Using mock.")
        else:
            print(f"[Reader] Real API returned {resp.status_code}. Using mock.")
    except Exception as e:
        print(f"[Reader] Real fetch error: {e}. Using mock.")

    return _mock_transactions()

def get_transaction_status(access_token: str, txn_id: str) -> Optional[str]:
    """Re-fetch a specific transaction status if possible. Returns None if not supported."""
    # PayPal Transaction Search does not support direct lookup by ID easily in this scope.
    # Return None to indicate verification not available for this call.
    return None

def _mock_transactions() -> List[Dict]:
    return [
        {"id": "MOCK-001", "amount": 120.50, "currency": "USD", "status": "DENIED", "decline_code": "DENIED", "retry_count": 0, "source": "mock"},
        {"id": "MOCK-002", "amount": 89.00, "currency": "USD", "status": "FAILED", "decline_code": "FAILED", "retry_count": 1, "source": "mock"},
        {"id": "MOCK-003", "amount": 250.00, "currency": "USD", "status": "PENDING", "decline_code": "PENDING", "retry_count": 0, "source": "mock"},
    ]

def create_test_order(access_token: str) -> Optional[str]:
    """Supported sandbox call — NOT a recovery of an existing failed transaction."""
    if not access_token:
        return None
    try:
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{"amount": {"currency_code": "USD", "value": "10.00"}}]
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
        print(f"[Order] Failed: {e}")
    return None
