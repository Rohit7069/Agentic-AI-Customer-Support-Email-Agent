"""Database service for CRUD operations."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.base import async_session
from src.db.models import Customer, Email, EmailResponse, HumanReview, FollowUp
from src.db.enums import (
    EmailStatusEnum, EmailPriorityEnum, ReviewStatusEnum,
    ReviewReasonEnum, FollowUpTypeEnum
)
from src.services.base import BaseService


class DatabaseService(BaseService):
    """Handles all database operations."""

    async def _get_session(self) -> AsyncSession:
        return async_session()

    async def get_or_create_customer(self, email: str, name: str = None) -> Customer:
        """Get existing customer or create a new one."""
        async with async_session() as session:
            result = await session.execute(
                select(Customer).where(Customer.email == email)
            )
            customer = result.scalar_one_or_none()
            if not customer:
                customer = Customer(email=email, name=name)
                session.add(customer)
                await session.commit()
                await session.refresh(customer)
            return customer

    async def create_email(
        self, sender: str, subject: str, body: str,
        customer_id: int = None, html_body: str = None
    ) -> Email:
        """Create a new email record."""
        async with async_session() as session:
            email = Email(
                sender=sender,
                subject=subject,
                body=body,
                customer_id=customer_id,
                html_body=html_body,
                status=EmailStatusEnum.PENDING,
                received_at=datetime.utcnow(),
            )
            session.add(email)
            await session.commit()
            await session.refresh(email)
            return email

    async def get_email(self, email_id: int) -> Optional[Email]:
        """Get an email by ID."""
        async with async_session() as session:
            result = await session.execute(
                select(Email).where(Email.id == email_id)
            )
            return result.scalar_one_or_none()

    async def update_email_classification(
        self, email_id: int, category: str,
        confidence: float, priority: str
    ) -> None:
        """Update email classification results."""
        async with async_session() as session:
            result = await session.execute(
                select(Email).where(Email.id == email_id)
            )
            email = result.scalar_one_or_none()
            if email:
                email.category = category
                email.confidence_score = confidence
                try:
                    email.priority = EmailPriorityEnum(priority)
                except ValueError:
                    email.priority = EmailPriorityEnum.MEDIUM
                email.status = EmailStatusEnum.CLASSIFIED
                await session.commit()

    async def update_email_status(self, email_id: int, status: EmailStatusEnum) -> None:
        """Update email processing status."""
        async with async_session() as session:
            result = await session.execute(
                select(Email).where(Email.id == email_id)
            )
            email = result.scalar_one_or_none()
            if email:
                email.status = status
                if status in [EmailStatusEnum.COMPLETED, EmailStatusEnum.FAILED]:
                    email.processed_at = datetime.utcnow()
                await session.commit()

    async def get_customer_emails(
        self, customer_id: int, limit: int = 5
    ) -> List[Email]:
        """Get recent emails for a customer."""
        async with async_session() as session:
            result = await session.execute(
                select(Email)
                .where(Email.customer_id == customer_id)
                .order_by(Email.received_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    async def get_recent_emails(self, limit: int = 20) -> List[Email]:
        """Get recent emails across all customers for history view."""
        async with async_session() as session:
            result = await session.execute(
                select(Email).order_by(Email.received_at.desc()).limit(limit)
            )
            return result.scalars().all()

    async def get_stats(self) -> dict:
        """Get system processing statistics."""
        async with async_session() as session:
            # Note: For simplicity in the demo, we fetch all and count in Python.
            # In production, use func.count() with group_by in the SQL query.
            result = await session.execute(select(Email))
            emails = result.scalars().all()
            
            total = len(emails)
            reviewed = len([e for e in emails if e.status == EmailStatusEnum.REVIEW_PENDING or e.status == EmailStatusEnum.REVIEW_APPROVED])
            auto = total - reviewed
            
            followups_res = await session.execute(select(FollowUp))
            followups = followups_res.scalars().all()
            
            return {
                "total": total,
                "auto": auto,
                "reviewed": reviewed,
                "followups": len(followups)
            }

    async def create_response(
        self, email_id: int, response_text: str,
        response_subject: str = None, model_used: str = None,
        tokens_used: int = 0, requires_review: bool = False
    ) -> EmailResponse:
        """Create a response record."""
        async with async_session() as session:
            response = EmailResponse(
                email_id=email_id,
                response_text=response_text,
                response_subject=response_subject,
                model_used=model_used,
                tokens_used=tokens_used,
                requires_review=requires_review,
            )
            session.add(response)
            await session.commit()
            await session.refresh(response)
            return response

    async def create_review(
        self, email_id: int, reason: str,
        original_response: str = None
    ) -> HumanReview:
        """Create a human review record."""
        async with async_session() as session:
            # Map reason string to enum
            reason_enum = None
            reason_map = {
                "Low classification confidence": ReviewReasonEnum.LOW_CONFIDENCE,
                "Escalated complaint": ReviewReasonEnum.ESCALATED_COMPLAINT,
                "Critical keywords detected": ReviewReasonEnum.CRITICAL_KEYWORDS,
                "Uncertain category": ReviewReasonEnum.UNCERTAIN_CATEGORY,
                "Response generation failed": ReviewReasonEnum.GENERATION_FAILED,
            }
            reason_enum = reason_map.get(reason, ReviewReasonEnum.LOW_CONFIDENCE)

            review = HumanReview(
                email_id=email_id,
                reason=reason_enum,
                review_reason_text=reason,
                original_response=original_response,
                status=ReviewStatusEnum.PENDING,
            )
            session.add(review)
            await session.commit()
            await session.refresh(review)
            return review

    async def approve_review(
        self, review_id: int, approved_response: str = None,
        reviewer_notes: str = None
    ) -> Optional[HumanReview]:
        """Approve a human review."""
        async with async_session() as session:
            result = await session.execute(
                select(HumanReview).where(HumanReview.id == review_id)
            )
            review = result.scalar_one_or_none()
            if review:
                review.status = ReviewStatusEnum.APPROVED
                review.approved_response = approved_response
                review.reviewer_notes = reviewer_notes
                review.reviewed_at = datetime.utcnow()
                await session.commit()
                await session.refresh(review)
            return review

    async def get_pending_reviews(self) -> List[HumanReview]:
        """Get all pending reviews."""
        async with async_session() as session:
            result = await session.execute(
                select(HumanReview)
                .where(HumanReview.status == ReviewStatusEnum.PENDING)
                .order_by(HumanReview.created_at.asc())
            )
            return result.scalars().all()

    async def create_followup(
        self, email_id: int, followup_type: FollowUpTypeEnum,
        scheduled_for: datetime, notes: str = None
    ) -> FollowUp:
        """Create a follow-up record."""
        async with async_session() as session:
            followup = FollowUp(
                email_id=email_id,
                followup_type=followup_type,
                scheduled_for=scheduled_for,
                notes=notes,
            )
            session.add(followup)
            await session.commit()
            await session.refresh(followup)
            return followup

    async def mark_response_sent(self, email_id: int) -> None:
        """Mark a response as sent."""
        async with async_session() as session:
            result = await session.execute(
                select(EmailResponse)
                .where(EmailResponse.email_id == email_id)
                .order_by(EmailResponse.created_at.desc())
            )
            response = result.scalar_one_or_none()
            if response:
                response.is_sent = True
                await session.commit()
