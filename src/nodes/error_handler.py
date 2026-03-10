"""Error handler node — logs errors and updates email status."""
import logging
from datetime import datetime
from src.graph.state import EmailAgentState
from src.services.database_service import DatabaseService
from src.db.enums import EmailStatusEnum

logger = logging.getLogger(__name__)


async def error_handler_node(state: EmailAgentState) -> dict:
    """Handle errors by logging and updating status."""
    error_message = state.get("error_message", "Unknown error")
    email_id = state.get("email_id")

    logger.error(
        f"Error processing email {email_id}: {error_message}"
    )

    try:
        if email_id:
            db_service = DatabaseService()
            await db_service.update_email_status(
                email_id, EmailStatusEnum.FAILED
            )
    except Exception as e:
        logger.error(f"Failed to update error status: {e}")

    return {
        "status": "failed",
        "error_message": error_message,
        "processing_completed_at": datetime.utcnow(),
    }
