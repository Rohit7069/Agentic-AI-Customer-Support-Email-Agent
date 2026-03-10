"""Review check node — determines if email needs human review."""
import logging
from src.graph.state import EmailAgentState

logger = logging.getLogger(__name__)


async def review_check_node(state: EmailAgentState) -> dict:
    """Determine if email needs human review based on rules."""
    category = state.get("category", "other")
    priority = state.get("priority", "medium")
    confidence = state.get("confidence_score", 1.0)
    body = state.get("body", "").lower()

    needs_review = False
    review_reason = None

    # Rule 1: Low confidence classification
    if confidence < 0.6:
        needs_review = True
        review_reason = "Low classification confidence"

    # Rule 2: Escalated complaints
    if category == "complaint" and priority in ["high", "urgent"]:
        needs_review = True
        review_reason = "Escalated complaint"

    # Rule 3: Critical keywords detected
    critical_keywords = [
        "urgent", "fire", "down", "broken", "help",
        "emergency", "asap", "critical"
    ]
    if any(keyword in body for keyword in critical_keywords):
        needs_review = True
        review_reason = "Critical keywords detected"

    # Rule 4: Uncertain categories
    if category == "other" and confidence < 0.8:
        needs_review = True
        review_reason = "Uncertain category"

    logger.info(
        f"Review check for email {state.get('email_id')}: "
        f"needs_review={needs_review}, reason={review_reason}"
    )

    return {
        "needs_human_review": needs_review,
        "review_reason": review_reason,
    }
