"""Review API routes."""
import logging
from fastapi import APIRouter, HTTPException
from src.api.schemas import ReviewRequest, ReviewResponse
from src.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("/pending")
async def get_pending_reviews():
    """Get all pending human reviews."""
    db_service = DatabaseService()
    reviews = await db_service.get_pending_reviews()

    response_list = []
    for review in reviews:
        # Fetch the original email for context
        email = await db_service.get_email(review.email_id)
        
        response_list.append(
            ReviewResponse(
                review_id=review.id,
                email_id=review.email_id,
                customer_email=email.sender if email else "Unknown",
                customer_subject=email.subject if email else "Unknown",
                customer_body=email.body if email else "Unknown",
                reason=review.review_reason_text,
                status=review.status.value if review.status else "pending",
                original_response=review.original_response,
                approved_response=review.approved_response,
                created_at=review.created_at,
            )
        )
        
    return response_list


from src.nodes.human_review import human_review_node
from src.nodes.response_sending import response_sending_node
from src.nodes.followup_scheduling import followup_scheduling_node
from src.graph.state import EmailAgentState

@router.post("/{review_id}/approve", response_model=ReviewResponse)
async def approve_review(review_id: int, request_body: ReviewRequest):
    """Approve a human review with optional modified response and resume workflow."""
    db_service = DatabaseService()
    
    # Get the review to find the email_id
    reviews = await db_service.get_pending_reviews()
    review_to_approve = next((r for r in reviews if r.id == review_id), None)
    
    if not review_to_approve:
        raise HTTPException(status_code=404, detail="Pending review not found")
        
    email = await db_service.get_email(review_to_approve.email_id)

    # 1. Update the database record
    review = await db_service.approve_review(
        review_id=review_id,
        approved_response=request_body.approved_response or review_to_approve.original_response,
        reviewer_notes=request_body.reviewer_notes,
    )

    # 2. Resume the workflow manually
    initial_state = EmailAgentState(
        email_id=email.id,
        review_id=review.id,
        generated_response=review.approved_response,
        sender=email.sender,
        category=email.category,
        priority=email.priority.value if email.priority else None,
    )
    
    # Execute the remaining nodes
    try:
        # Node: Human Review (logs approval, sets final_response)
        state_update_1 = await human_review_node(initial_state)
        initial_state.update(state_update_1)
        
        # Node: Response Sending
        state_update_2 = await response_sending_node(initial_state)
        initial_state.update(state_update_2)
        
        # Node: Follow-up Scheduling
        if initial_state.get("status") == "responded":
            state_update_3 = await followup_scheduling_node(initial_state)
            initial_state.update(state_update_3)
            
    except Exception as e:
        logger.error(f"Failed to resume workflow after review: {e}")

    return ReviewResponse(
        review_id=review.id,
        email_id=review.email_id,
        reason=review.review_reason_text,
        status=review.status.value if review.status else "approved",
        original_response=review.original_response,
        approved_response=review.approved_response,
        created_at=review.created_at,
    )
