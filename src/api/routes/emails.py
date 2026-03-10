"""Email API routes."""
import time
import logging
from fastapi import APIRouter, Request, HTTPException
from src.api.schemas import (
    TestEmailRequest, TestEmailResponse, EmailStatusResponse
)
from src.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emails", tags=["emails"])


@router.post("/test", response_model=TestEmailResponse)
async def test_email(request_body: TestEmailRequest, request: Request):
    """Submit a test email and run the full workflow pipeline."""
    start_time = time.time()

    try:
        db_service = DatabaseService()

        # Get or create customer
        customer = await db_service.get_or_create_customer(
            email=request_body.sender
        )

        # Create the email record
        email_db = await db_service.create_email(
            sender=request_body.sender,
            subject=request_body.subject,
            body=request_body.body,
            customer_id=customer.id,
            html_body=request_body.html_body,
        )

        # Run the entire LangGraph workflow
        workflow = request.app.state.workflow
        final_state = await workflow.ainvoke({"email_id": email_db.id})

        processing_time = (time.time() - start_time) * 1000

        return TestEmailResponse(
            email_id=email_db.id,
            category=final_state.get("category"),
            priority=final_state.get("priority"),
            confidence_score=final_state.get("confidence_score"),
            generated_response=final_state.get("generated_response"),
            needs_human_review=final_state.get("needs_human_review", False),
            review_reason=final_state.get("review_reason"),
            status=final_state.get("status", "unknown"),
            followup_scheduled=final_state.get("followup_scheduled", False),
            processing_time_ms=round(processing_time, 2),
        )

    except Exception as e:
        logger.error(f"Email processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from src.api.schemas import HistoryResponse, EmailDetailsResponse

@router.get("/history", response_model=HistoryResponse)
async def get_history():
    """Get overall processing statistics and email history."""
    db_service = DatabaseService()
    
    stats = await db_service.get_stats()
    emails = await db_service.get_recent_emails(limit=50)
    
    history_items = [
        {
            "id": e.id,
            "sender": e.sender,
            "subject": e.subject,
            "category": e.category,
            "priority": e.priority.value if e.priority else None,
            "status": e.status.value if e.status else "unknown",
        }
        for e in emails
    ]
    
    return {
        "stats": stats,
        "history": history_items
    }

@router.get("/{email_id}", response_model=EmailDetailsResponse)
async def get_email_details(email_id: int):
    """Get full details of a processed email."""
    # We will query the DB directly here for simplicity to join the tables
    from sqlalchemy import select
    from src.db.models import Email, EmailResponse, HumanReview, FollowUp
    from src.db.base import async_session
    
    async with async_session() as session:
        # Get Email
        result = await session.execute(select(Email).where(Email.id == email_id))
        email = result.scalar_one_or_none()
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
            
        # Get Response
        result = await session.execute(select(EmailResponse).where(EmailResponse.email_id == email_id).order_by(EmailResponse.created_at.desc()))
        response = result.scalars().first()
        
        # Get Review
        result = await session.execute(select(HumanReview).where(HumanReview.email_id == email_id).order_by(HumanReview.created_at.desc()))
        review = result.scalars().first()
        
        # Get FollowUp
        result = await session.execute(select(FollowUp).where(FollowUp.email_id == email_id).order_by(FollowUp.created_at.desc()))
        followup = result.scalars().first()
        
        return EmailDetailsResponse(
            id=email.id,
            sender=email.sender,
            subject=email.subject,
            body=email.body,
            category=email.category,
            priority=getattr(email.priority, 'value', email.priority) if email.priority else None,
            confidence_score=email.confidence_score,
            status=getattr(email.status, 'value', email.status) if email.status else "unknown",
            received_at=email.received_at,
            processed_at=email.processed_at,
            
            ai_response=response.response_text if response else None,
            model_used=response.model_used if response else None,
            
            human_reviewed=review is not None and getattr(review.status, 'value', review.status) == "approved",
            reviewer_notes=review.reviewer_notes if review else None,
            
            followup_scheduled=followup is not None,
            followup_date=followup.scheduled_for if followup else None,
        )

@router.get("/{email_id}/status", response_model=EmailStatusResponse)
async def get_email_status(email_id: int):
    """Get the processing status of an email."""
    db_service = DatabaseService()
    email = await db_service.get_email(email_id)

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    return EmailStatusResponse(
        email_id=email.id,
        sender=email.sender,
        subject=email.subject,
        category=email.category,
        priority=email.priority.value if email.priority else None,
        status=email.status.value if email.status else "unknown",
        created_at=email.created_at,
        processed_at=email.processed_at,
    )
