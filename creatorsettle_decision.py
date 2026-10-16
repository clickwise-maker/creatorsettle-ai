"""
CreatorSettle AI — Decision Engine
Deterministic core + optional real LLM enhancement.
"""

import os
from typing import Dict, Tuple, Optional
import requests

def decide(transaction: Dict) -> Tuple[str, float, str]:
    """Core deterministic decision (always works)."""
    code = transaction.get("decline_code")
    retries = transaction.get("retry_count", 0)

    if code is None:
        return "HOLD", 0.4, "No clear decline reason — hold for manual review."

    if code in ("FRAUD_FILTER", "FRAUD"):
        return "ALERT", 0.95, "Possible fraud flag — human review required."

    if code in ("EXPIRED_CARD", "EXPIRED"):
        return "ALERT", 0.90, "Card expired — ask creator to update payment method."

    if code == "INSUFFICIENT_FUNDS":
        if retries >= 2:
            return "ALERT", 0.85, "Repeated insufficient funds — manual intervention needed."
        return "ROUTE", 0.80, "Insufficient funds — suggest alternate funding source."

    if retries >= 1:
        return "ALERT", 0.70, f"Unknown decline ({code}) after retry — escalate."
    return "RETRY", 0.65, f"Unknown decline ({code}) — safe to retry once."

class LLMClient:
    """Simple OpenAI-compatible or xAI client."""
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("XAI_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        if "x.ai" in self.base_url or os.getenv("XAI_API_KEY"):
            self.base_url = "https://api.x.ai/v1"
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini" if "openai" in self.base_url else "grok-beta")

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
                    "temperature": 0.3,
                    "max_tokens": 80,
                },
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LLM] Error: {e}")
            return None

def decide_with_ai(transaction: Dict, llm_client: Optional[LLMClient] = None) -> Tuple[str, float, str]:
    """
    Deterministic decision + optional real LLM message refinement.
    """
    action, conf, msg = decide(transaction)

    if llm_client is None:
        llm_client = LLMClient()

    if not llm_client.api_key:
        return action, conf, msg + " (deterministic)"

    prompt = f"""You are a payments recovery assistant for creators.
Transaction: {transaction}
Recommended action: {action}
Write a short, clear one-line message for the creator explaining why. Do not change the action."""
    enhanced = llm_client.complete(prompt)
    if enhanced:
        return action, conf, enhanced.strip()
    return action, conf, msg + " (LLM failed, used rules)"
