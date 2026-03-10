"""Response sending node — sends the email response."""
import logging
from src.graph.state import EmailAgentState
from src.services.email_service import EmailService
from src.services.database_service import DatabaseService
from src.db.enums import EmailStatusEnum

logger = logging.getLogger(__name__)


async def response_sending_node(state: EmailAgentState) -> dict:
    """Send the final response email."""
    try:
        sender = state.get("sender", "")
        response_subject = state.get("response_subject", "Re: Your inquiry")
        final_response = state.get("final_response") or state.get("generated_response", "")

        if not final_response:
            return {
                "error_message": "No response to send",
                "response_sent": False,
                "status": "failed",
            }

        # Send the email
        email_service = EmailService()
        result = await email_service.send_email(
            to=sender,
            subject=response_subject,
            body=final_response,
        )

        if result.get("success"):
            db_service = DatabaseService()
            await db_service.update_email_status(
                state.get("email_id"), EmailStatusEnum.RESPONDED
            )
            await db_service.mark_response_sent(state.get("email_id"))

            logger.info(f"Response sent for email {state.get('email_id')}")

            return {
                "response_sent": True,
                "final_response": final_response,
                "status": "responded",
            }
        else:
            return {
                "error_message": "Failed to send email",
                "response_sent": False,
                "status": "failed",
            }

    except Exception as e:
        logger.error(f"Response sending failed: {e}")
        return {
            "error_message": f"Response sending failed: {str(e)}",
            "response_sent": False,
            "status": "failed",
        }
