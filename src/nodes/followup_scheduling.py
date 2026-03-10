"""Follow-up scheduling node — schedules follow-ups based on category/priority."""
import logging
from datetime import datetime, timedelta
from src.graph.state import EmailAgentState
from src.services.database_service import DatabaseService
from src.db.enums import FollowUpTypeEnum, EmailStatusEnum

logger = logging.getLogger(__name__)

# Mapping of category to follow-up configuration
FOLLOWUP_CONFIG = {
    "technical_support": {
        "type": FollowUpTypeEnum.CHECK_RESOLUTION,
        "days": 2,
        "note": "Check if the technical issue was resolved",
    },
    "billing": {
        "type": FollowUpTypeEnum.BILLING_CONFIRMATION,
        "days": 3,
        "note": "Confirm billing issue resolution",
    },
    "complaint": {
        "type": FollowUpTypeEnum.SATISFACTION_SURVEY,
        "days": 5,
        "note": "Send satisfaction survey after complaint resolution",
    },
    "product_inquiry": {
        "type": FollowUpTypeEnum.CHECK_RESOLUTION,
        "days": 7,
        "note": "Follow up on product inquiry",
    },
    "feedback": {
        "type": FollowUpTypeEnum.FEEDBACK_ACKNOWLEDGMENT,
        "days": 1,
        "note": "Acknowledge customer feedback",
    },
}

# Priority multiplier for follow-up urgency
PRIORITY_MULTIPLIER = {
    "urgent": 0.5,
    "high": 0.75,
    "medium": 1.0,
    "low": 1.5,
}


async def followup_scheduling_node(state: EmailAgentState) -> dict:
    """Schedule follow-ups based on category and priority."""
    try:
        category = state.get("category", "other")
        priority = state.get("priority", "medium")
        email_id = state.get("email_id")

        config = FOLLOWUP_CONFIG.get(category)

        if config:
            multiplier = PRIORITY_MULTIPLIER.get(priority, 1.0)
            days = max(1, int(config["days"] * multiplier))
            scheduled_for = datetime.utcnow() + timedelta(days=days)

            db_service = DatabaseService()
            followup = await db_service.create_followup(
                email_id=email_id,
                followup_type=config["type"],
                scheduled_for=scheduled_for,
                notes=config["note"],
            )

            await db_service.update_email_status(
                email_id, EmailStatusEnum.COMPLETED
            )

            logger.info(
                f"Scheduled {config['type'].value} follow-up for email "
                f"{email_id} on {scheduled_for.strftime('%Y-%m-%d')}"
            )

            return {
                "followup_scheduled": True,
                "status": "completed",
                "processing_completed_at": datetime.utcnow(),
            }
        else:
            # No follow-up needed for 'other' category
            db_service = DatabaseService()
            await db_service.update_email_status(
                email_id, EmailStatusEnum.COMPLETED
            )

            logger.info(
                f"No follow-up needed for email {email_id} (category: {category})"
            )

            return {
                "followup_scheduled": False,
                "status": "completed",
                "processing_completed_at": datetime.utcnow(),
            }

    except Exception as e:
        logger.error(f"Follow-up scheduling failed: {e}")
        return {
            "followup_scheduled": False,
            "status": "completed",
            "processing_completed_at": datetime.utcnow(),
        }
