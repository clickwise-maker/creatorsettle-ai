"""
CreatorSettle AI — PayPal subscription recovery.
Supported real action: capture an outstanding balance on a PayPal subscription.
This is NOT recovery of arbitrary failed one-time payments.
"""
import hashlib
import os
import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com").rstrip("/")
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
_SUBSCRIPTION_RE = re.compile(r"^[A-Za-z0-9_-]{5,64}$")


def _valid_base_url() -> bool:
    parsed = urlparse(BASE_URL)
    return parsed.scheme == "https" and bool(parsed.netloc)


def get_access_token() -> Optional[str]:
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    secret = os.getenv("PAYPAL_SECRET")
    if not client_id or not secret or not _valid_base_url():
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
    except Exception:
        # Never print credentials, tokens, or raw authentication responses.
        return None


def _validate_capture(subscription_id: str, amount: str, currency: str) -> Optional[str]:
    if not isinstance(subscription_id, str) or not _SUBSCRIPTION_RE.fullmatch(subscription_id):
        return "invalid_subscription_id"
    if not isinstance(currency, str) or not _CURRENCY_RE.fullmatch(currency):
        return "invalid_currency"
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        return "invalid_amount"
    if not value.is_finite() or value <= 0 or value.as_tuple().exponent < -2:
        return "invalid_amount"
    if len(format(value, "f").split(".")[0]) > 10:
        return "invalid_amount"
    return None


def capture_outstanding_balance(
    subscription_id: str,
    amount: str,
    currency: str = "USD",
    note: str = "Capture outstanding balance",
    request_id: Optional[str] = None,
) -> Dict:
    """
    Submit one PayPal outstanding-balance capture request.
    PayPal-Request-Id makes retries of the same request idempotent within PayPal's
    documented retention window. A 202 means accepted, not confirmed.
    """
    invalid = _validate_capture(subscription_id, amount, currency)
    if invalid:
        return {"success": False, "state": "FAILED", "reason": invalid, "raw": None}
    if not _valid_base_url():
        return {"success": False, "state": "FAILED", "reason": "invalid_paypal_base_url", "raw": None}

    normalized_amount = format(Decimal(str(amount)), ".2f")
    if not request_id:
        # Stable key for direct callers; the dashboard passes its persisted approval ID.
        digest = hashlib.sha256(f"{subscription_id}|{normalized_amount}|{currency}".encode("utf-8")).hexdigest()[:32]
        request_id = "CS-" + digest
    if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,38}", request_id):
        return {"success": False, "state": "FAILED", "reason": "invalid_request_id", "raw": None}

    token = get_access_token()
    if not token:
        return {"success": False, "state": "FAILED", "reason": "no_oauth_token", "raw": None}

    payload = {
        "note": str(note)[:255],
        "capture_type": "OUTSTANDING_BALANCE",
        "amount": {"value": normalized_amount, "currency_code": currency},
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/v1/billing/subscriptions/{subscription_id}/capture",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "PayPal-Request-Id": request_id,
            },
            json=payload,
            timeout=20,
        )
        try:
            raw = resp.json()
        except Exception:
            raw = {"body": resp.text[:1000]}

        if resp.status_code == 202:
            return {"success": True, "state": "REQUEST_ACCEPTED", "reason": "request_accepted_pending_verification",
                    "status_code": resp.status_code, "request_id": request_id, "raw": raw}
        if resp.status_code in (200, 201):
            api_status = raw.get("status") if isinstance(raw, dict) else None
            if str(api_status).upper() == "COMPLETED":
                return {"success": True, "state": "CAPTURE_CONFIRMED", "reason": "capture_confirmed",
                        "status_code": resp.status_code, "request_id": request_id, "raw": raw}
            return {"success": True, "state": "REQUEST_ACCEPTED", "reason": "response_requires_verification",
                    "status_code": resp.status_code, "request_id": request_id, "raw": raw}
        return {"success": False, "state": "FAILED", "reason": "api_error",
                "status_code": resp.status_code, "request_id": request_id, "raw": raw}
    except requests.RequestException:
        # Outcome may be ambiguous after a timeout; do not auto-retry a money movement.
        return {"success": False, "state": "OUTCOME_UNKNOWN", "reason": "network_error_outcome_unknown",
                "request_id": request_id, "raw": None}


def get_subscription_details(subscription_id: str) -> Optional[Dict]:
    """Fetch a subscription for a later manual verification step."""
    if not isinstance(subscription_id, str) or not _SUBSCRIPTION_RE.fullmatch(subscription_id):
        return None
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
    except requests.RequestException:
        pass
    return None
