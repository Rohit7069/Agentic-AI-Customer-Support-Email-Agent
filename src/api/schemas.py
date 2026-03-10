"""Pydantic schemas for API request/response models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class TestEmailRequest(BaseModel):
    """Request body for submitting a test email."""
    sender: str = Field(..., description="Sender email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body text")
    html_body: Optional[str] = Field(None, description="Optional HTML body")


class TestEmailResponse(BaseModel):
    """Response after processing a test email through the workflow."""
    email_id: int
    category: Optional[str] = None
    priority: Optional[str] = None
    confidence_score: Optional[float] = None
    generated_response: Optional[str] = None
    needs_human_review: bool = False
    review_reason: Optional[str] = None
    status: str = "unknown"
    followup_scheduled: bool = False
    processing_time_ms: Optional[float] = None


class EmailStatusResponse(BaseModel):
    """Response for email status queries."""
    email_id: int
    sender: str
    subject: str
    category: Optional[str] = None
    priority: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class ReviewRequest(BaseModel):
    """Request body for approving/rejecting a review."""
    approved_response: Optional[str] = Field(
        None, description="Modified response text (optional)"
    )
    reviewer_notes: Optional[str] = Field(
        None, description="Notes from the reviewer"
    )


class ReviewResponse(BaseModel):
    """Response for review operations."""
    review_id: int
    email_id: int
    customer_email: Optional[str] = None
    customer_subject: Optional[str] = None
    customer_body: Optional[str] = None
    reason: Optional[str] = None
    status: str
    original_response: Optional[str] = None
    approved_response: Optional[str] = None
    created_at: Optional[datetime] = None


from typing import Optional, List

class StatsResponse(BaseModel):
    total: int
    auto: int
    reviewed: int
    followups: int

class HistoryItemResponse(BaseModel):
    id: int
    sender: str
    subject: str
    category: Optional[str] = None
    priority: Optional[str] = None
    status: str
    is_human_reviewed: bool = False

class HistoryResponse(BaseModel):
    stats: StatsResponse
    history: List[HistoryItemResponse]

class EmailDetailsResponse(BaseModel):
    id: int
    sender: str
    subject: str
    body: str
    category: Optional[str] = None
    priority: Optional[str] = None
    confidence_score: Optional[float] = None
    status: str
    received_at: datetime
    processed_at: Optional[datetime] = None
    
    # Response Data
    ai_response: Optional[str] = None
    model_used: Optional[str] = None
    
    # Review Data
    human_reviewed: bool = False
    reviewer_notes: Optional[str] = None
    
    # Follow-up Data
    followup_scheduled: bool = False
    followup_date: Optional[datetime] = None

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime
