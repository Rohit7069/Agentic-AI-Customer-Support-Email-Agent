"""Guardrails node — scans for prompt injection and PII."""
import logging
import re
from src.graph.state import EmailAgentState
from src.db.enums import ReviewReasonEnum

logger = logging.getLogger(__name__)

# Basic patterns for prompt injection
INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"system prompt",
    r"forget what you were told",
    r"you are now a",
    r"output the hidden",
    r"new instructions",
]

# Basic regex for PII (Credit Cards, SSN-like)
PII_PATTERNS = {
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
}


async def guardrails_node(state: EmailAgentState) -> dict:
    """Validate input email for safety and PII."""
    try:
        body = state.get("body", "").lower()
        email_id = state.get("email_id")
        
        # 1. Check for Prompt Injection
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, body):
                logger.warning(f"Potential prompt injection detected in email {email_id}")
                return {
                    "needs_human_review": True,
                    "review_reason": "Potential security threat detected in email content.",
                    "status": "safety_flagged"
                }

        # 2. Check for PII
        detected_pii = []
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, body):
                detected_pii.append(pii_type)
        
        if detected_pii:
            logger.info(f"PII detected in email {email_id}: {detected_pii}")
            return {
                "needs_human_review": True,
                "review_reason": f"Sensitive information ({', '.join(detected_pii)}) detected.",
                "status": "pii_flagged"
            }

        return {"status": "safety_passed"}

    except Exception as e:
        logger.error(f"Guardrails node failed: {e}")
        return {
            "error_message": f"Guardrails failed: {str(e)}",
            "status": "failed"
        }
