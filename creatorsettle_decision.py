"""
CreatorSettle AI — Decision Engine
Chooses RETRY / ROUTE / ALERT / HOLD based on decline reason and history.
"""

from typing import Dict, Tuple

def decide(transaction: Dict) -> Tuple[str, float, str]:
    code = transaction.get("decline_code")
    retries = transaction.get("retry_count", 0)

    if code is None:
        return "HOLD", 0.4, "No clear decline reason — hold for manual review."

    if code == "FRAUD_FILTER":
        return "ALERT", 0.95, "Possible fraud flag — human review required."

    if code == "EXPIRED_CARD":
        return "ALERT", 0.90, "Card expired — ask creator to update payment method."

    if code == "INSUFFICIENT_FUNDS":
        if retries >= 2:
            return "ALERT", 0.85, "Repeated insufficient funds — manual intervention needed."
        return "ROUTE", 0.80, "Insufficient funds — try alternate funding source."

    # Default
    if retries >= 1:
        return "ALERT", 0.70, f"Unknown decline ({code}) after retry — escalate."
    return "RETRY", 0.65, f"Unknown decline ({code}) — safe to retry once."
