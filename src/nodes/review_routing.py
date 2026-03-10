"""Review routing node — creates review record and routes for human approval."""
import logging
from src.graph.state import EmailAgentState
from src.services.database_service import DatabaseService
from src.db.enums import EmailStatusEnum

logger = logging.getLogger(__name__)


async def review_routing_node(state: EmailAgentState) -> dict:
    """Create review record and route for human review."""
    try:
        db_service = DatabaseService()

        review = await db_service.create_review(
            email_id=state.get("email_id"),
            reason=state.get("review_reason", "Unknown"),
            original_response=state.get("generated_response"),
        )

        await db_service.update_email_status(
            state.get("email_id"), EmailStatusEnum.REVIEW_PENDING
        )

        logger.info(
            f"Routed email {state.get('email_id')} for review: "
            f"review_id={review.id}, reason={state.get('review_reason')}"
        )

        return {
            "review_id": review.id,
            "status": "review_pending",
        }

    except Exception as e:
        logger.error(f"Review routing failed: {e}")
        return {
            "error_message": f"Review routing failed: {str(e)}",
            "status": "failed",
        }
