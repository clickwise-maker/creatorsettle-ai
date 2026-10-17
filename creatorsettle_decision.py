"""
CreatorSettle AI — Decision Engine
Honest: RETRY only when real recovery is supported. Otherwise instruction.
"""

import os
from typing import Dict, Tuple, Optional
import requests

def classify_failure(status: Optional[str]) -> str:
    if not status:
        return "UNKNOWN"
    s = status.upper()
    if s in ("DENIED", "FAILED", "DECLINED", "VOIDED"):
        return "FAILED"
    if s in ("PENDING", "PROCESSING"):
        return "PENDING"
    return "UNKNOWN"

def decide(transaction: Dict) -> Tuple[str, float, str, str]:
    """
    Returns: action, confidence, message, execution_type
    execution_type: "instruction" | "none"
    Note: Real recovery of an existing failed transaction is not supported
    by the available Sandbox scope. Therefore RETRY never uses a fake order.
    """
    code = classify_failure(transaction.get("decline_code") or transaction.get("status"))
    retries = transaction.get("retry_count", 0)
    source = transaction.get("source", "unknown")

    if code == "FAILED":
        if retries == 0:
            return (
                "RETRY",
                0.65,
                f"Failed status detected (source={source}). No supported API to retry this exact transaction. Seller should review in PayPal dashboard.",
                "instruction",
            )
        return (
            "ESCALATE",
            0.75,
            "Already attempted — escalate to seller for manual review.",
            "instruction",
        )

    if code == "PENDING":
        return "HOLD", 0.60, "Still pending — do not act.", "none"

    return "HOLD", 0.40, "Unclear status — check PayPal dashboard.", "instruction"

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
    prompt = f"""Payments recovery assistant.
Transaction: {transaction}
Action: {action}
Write a short seller message. Do not claim recovery happened."""
    enhanced = llm_client.complete(prompt)
    if enhanced:
        return action, conf, enhanced.strip(), exec_type
    return action, conf, msg + " (LLM unavailable)", exec_type
