"""
CreatorSettle AI — Decision Engine
Honest actions: RETRY / ROUTE / HOLD / ESCALATE
Where PayPal does not support automatic recovery, return a safe instruction instead of fake success.
"""

import os
from typing import Dict, Tuple, Optional
import requests

def classify_failure(status: Optional[str]) -> str:
    """Map real PayPal-like statuses to internal codes."""
    if not status:
        return "UNKNOWN"
    s = status.upper()
    if s in ("DENIED", "FAILED", "DECLINED"):
        return "FAILED"
    if "INSUFFICIENT" in s or "FUNDS" in s:
        return "INSUFFICIENT_FUNDS"
    if "EXPIRED" in s or "CARD" in s:
        return "EXPIRED_CARD"
    if "FRAUD" in s or "RISK" in s:
        return "FRAUD_FILTER"
    if s in ("PENDING", "PROCESSING"):
        return "PENDING"
    return s

def decide(transaction: Dict) -> Tuple[str, float, str, str]:
    """
    Returns: action, confidence, message, execution_type
    execution_type: "api" | "instruction" | "none"
    """
    code = classify_failure(transaction.get("decline_code") or transaction.get("status"))
    retries = transaction.get("retry_count", 0)

    if code in ("FRAUD_FILTER", "RISK"):
        return "ESCALATE", 0.95, "Fraud/risk flag — stop and ask seller to review.", "none"

    if code == "EXPIRED_CARD":
        return "ESCALATE", 0.90, "Payment method expired — seller must update card. No auto-retry.", "instruction"

    if code == "INSUFFICIENT_FUNDS":
        if retries >= 2:
            return "ESCALATE", 0.85, "Repeated insufficient funds — ask seller to add funds or change method.", "instruction"
        return "ROUTE", 0.80, "Insufficient funds — suggest seller try a different funding source.", "instruction"

    if code in ("FAILED", "DENIED", "DECLINED"):
        if retries == 0:
            return "RETRY", 0.70, "Transient failure — safe to retry once via Orders API.", "api"
        return "ESCALATE", 0.75, "Retry already attempted — escalate to seller.", "instruction"

    if code == "PENDING":
        return "HOLD", 0.60, "Payment still pending — do not retry yet.", "none"

    return "HOLD", 0.40, "Unclear status — hold and ask seller to check PayPal dashboard.", "instruction"

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("XAI_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        if os.getenv("XAI_API_KEY"):
            self.base_url = "https://api.x.ai/v1"
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def complete(self, prompt: str) -> Optional[str]:
        if not self.api_key:
            return None
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 100,
                },
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            return None

def decide_with_ai(transaction: Dict, llm_client: Optional[LLMClient] = None) -> Tuple[str, float, str, str]:
    action, conf, msg, exec_type = decide(transaction)
    if llm_client is None:
        llm_client = LLMClient()
    if not llm_client.api_key:
        return action, conf, msg + " (rules)", exec_type

    prompt = f"""You are a payments recovery assistant.
Transaction: {transaction}
Recommended action: {action}
Execution type: {exec_type}
Write a short clear message for the seller. Do not claim money was recovered if execution_type is not 'api'."""
    enhanced = llm_client.complete(prompt)
    if enhanced:
        return action, conf, enhanced.strip(), exec_type
    return action, conf, msg + " (LLM unavailable)", exec_type
