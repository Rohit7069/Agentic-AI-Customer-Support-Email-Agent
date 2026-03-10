"""Email retrieval node — fetches email from DB and populates state."""
import logging
from datetime import datetime
from src.graph.state import EmailAgentState
from src.services.database_service import DatabaseService
from src.db.enums import EmailStatusEnum

logger = logging.getLogger(__name__)


async def email_retrieval_node(state: EmailAgentState) -> dict:
    """Retrieve email from database and populate state."""
    try:
        email_id = state.get("email_id")
        if not email_id:
            return {
                "error_message": "No email_id provided",
                "status": "failed",
            }

        db_service = DatabaseService()
        email = await db_service.get_email(email_id)

        if not email:
            return {
                "error_message": f"Email {email_id} not found",
                "status": "failed",
            }

        # Update status to processing
        await db_service.update_email_status(email_id, EmailStatusEnum.PROCESSING)

        logger.info(f"Retrieved email {email_id}: {email.subject}")

        return {
            "email_id": email.id,
            "sender": email.sender,
            "subject": email.subject,
            "body": email.body,
            "html_body": email.html_body,
            "received_at": email.received_at,
            "customer_id": email.customer_id,
            "status": "processing",
            "processing_started_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Email retrieval failed: {e}")
        return {
            "error_message": f"Email retrieval failed: {str(e)}",
            "status": "failed",
        }
