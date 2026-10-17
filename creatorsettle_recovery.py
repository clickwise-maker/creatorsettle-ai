"""
CreatorSettle AI — Real Recovery Module
Supported real action: capture outstanding balance on a suspended PayPal subscription.
Does not claim recovery of arbitrary failed one-time payments.
"""

import os
import requests
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

def get_access_token() -> Optional[str]:
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    secret = os.getenv("PAYPAL_SECRET")
    if not client_id or not secret:
        return None
    try:
        resp = requests.post(
            f"{BASE_URL}/v1/oauth2/token",
            auth=(client_id, secret),
            headers={"Accept": "application/json"},
            data={"grant_type": "client_credentials"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        print(f"[OAuth] {e}")
        return None

def capture_outstanding_balance(subscription_id: str, amount: str, currency: str = "USD", note: str = "Capture outstanding balance") -> Dict:
    """
    Real PayPal API call.
    POST /v1/billing/subscriptions/{id}/capture
    Returns result with success flag and raw response.
    """
    token = get_access_token()
    if not token:
        return {"success": False, "reason": "no_oauth_token", "raw": None}

    url = f"{BASE_URL}/v1/billing/subscriptions/{subscription_id}/capture"
    payload = {
        "note": note,
        "capture_type": "OUTSTANDING_BALANCE",
        "amount": {"value": amount, "currency_code": currency},
    }
    try:
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=20,
        )
        raw = None
        try:
            raw = resp.json()
        except Exception:
            raw = resp.text
        success = resp.status_code in (200, 201, 202)
        return {
            "success": success,
            "status_code": resp.status_code,
            "reason": "captured" if success else "api_error",
            "raw": raw,
        }
    except Exception as e:
        return {"success": False, "reason": str(e), "raw": None}

def get_subscription_details(subscription_id: str) -> Optional[Dict]:
    """Fetch subscription to verify status after capture attempt."""
    token = get_access_token()
    if not token:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/v1/billing/subscriptions/{subscription_id}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None
