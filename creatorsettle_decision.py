"""
CreatorSettle AI — Decision Engine
Deterministic core + optional LLM enhancement.
"""

import os
from typing import Dict, Tuple, Optional

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

def decide_with_ai(transaction: Dict, llm_client=None) -> Tuple[str, float, str]:
    """
    Optional AI enhancement.
    If llm_client is provided and has a complete() method, it can refine the message.
    Falls back to deterministic decision.
    """
    action, conf, msg = decide(transaction)
    if llm_client is None:
        return action, conf, msg + " (deterministic)"

    try:
        prompt = f"""You are a payments recovery assistant.
Transaction: {transaction}
Current decision: {action}
Give a short, clear one-line reason for the creator. Do not change the action."""
        enhanced = llm_client.complete(prompt)
        if enhanced:
            return action, conf, enhanced.strip()
    except Exception:
        pass
    return action, conf, msg + " (AI unavailable, used rules)"
