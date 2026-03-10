"""Human review node — simulated auto-approval for demo purposes."""
import logging
from src.graph.state import EmailAgentState
from src.services.database_service import DatabaseService
from src.db.enums import EmailStatusEnum

logger = logging.getLogger(__name__)


async def human_review_node(state: EmailAgentState) -> dict:
    """Simulate human review approval.

    In production, this would pause the workflow and wait for
    a human to approve/reject/modify the response via the API.
    For demo purposes, we auto-approve the generated response.
    """
    try:
        review_id = state.get("review_id")
        generated_response = state.get("generated_response", "")

        if review_id:
            db_service = DatabaseService()
            await db_service.approve_review(
                review_id=review_id,
                approved_response=generated_response,
                reviewer_notes="Auto-approved for demo",
            )
            await db_service.update_email_status(
                state.get("email_id"), EmailStatusEnum.REVIEW_APPROVED
            )

        logger.info(
            f"Auto-approved review {review_id} for email {state.get('email_id')}"
        )

        return {
            "approved_response": generated_response,
            "final_response": generated_response,
            "status": "review_approved",
        }

    except Exception as e:
        logger.error(f"Human review processing failed: {e}")
        return {
            "error_message": f"Human review failed: {str(e)}",
            "status": "failed",
        }
