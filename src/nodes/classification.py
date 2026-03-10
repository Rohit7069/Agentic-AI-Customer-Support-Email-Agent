"""Classification node — classifies email category and assesses priority."""
import logging
from src.graph.state import EmailAgentState
from src.services.llm_service import LLMService
from src.services.database_service import DatabaseService

logger = logging.getLogger(__name__)


async def classification_node(state: EmailAgentState) -> dict:
    """Classify email and assess priority."""
    try:
        subject = state.get("subject", "")
        body = state.get("body", "")

        llm_service = LLMService()

        # Classify email into categories
        classification_result = await llm_service.classify_email(subject, body)
        category = classification_result.get("category", "other")
        confidence = classification_result.get("confidence_score", 0.0)

        # Assess priority separately
        priority_result = await llm_service.assess_priority(body)
        priority = priority_result.get("priority", "medium")

        # Persist to database
        db_service = DatabaseService()
        await db_service.update_email_classification(
            state.get("email_id"), category, confidence, priority
        )

        logger.info(
            f"Classified email {state.get('email_id')}: "
            f"category={category}, priority={priority}, confidence={confidence}"
        )

        return {
            "category": category,
            "priority": priority,
            "confidence_score": confidence,
        }

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return {
            "error_message": f"Classification failed: {str(e)}",
            "category": "other",
            "priority": "medium",
            "confidence_score": 0.0,
        }
