"""Simulated email sending service."""
import logging
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class EmailService(BaseService):
    """Simulated email sending service.

    In production, this would integrate with SMTP, SendGrid, AWS SES, etc.
    For demo purposes, it logs the email to console.
    """

    async def send_email(
        self, to: str, subject: str, body: str
    ) -> dict:
        """Send an email (simulated)."""
        logger.info(
            f"\n{'='*60}\n"
            f"📧 SENDING EMAIL\n"
            f"{'='*60}\n"
            f"To: {to}\n"
            f"Subject: {subject}\n"
            f"{'─'*60}\n"
            f"{body}\n"
            f"{'='*60}\n"
        )
        return {
            "success": True,
            "message": f"Email sent to {to}",
        }
