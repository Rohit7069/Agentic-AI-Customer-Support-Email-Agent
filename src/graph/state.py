"""LangGraph state definition for the email agent."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from typing_extensions import TypedDict


class EmailAgentState(TypedDict, total=False):
    """State object passed through LangGraph nodes.

    Using total=False so every field is optional — nodes can return
    partial state updates without needing to populate every field.
    """

    # Input Information
    email_id: int
    sender: str
    subject: str
    body: str
    html_body: Optional[str]
    received_at: datetime

    # Classification Results
    category: Optional[str]
    priority: Optional[str]
    confidence_score: Optional[float]

    # Context Information
    customer_id: Optional[int]
    customer_history: Optional[List[Dict[str, Any]]]
    kb_results: Optional[List[Dict[str, Any]]]
    context_summary: Optional[str]

    # Response Generation
    generated_response: Optional[str]
    response_subject: Optional[str]
    response_attempt: int
    model_used: Optional[str]
    tokens_used: int

    # Review Workflow
    needs_human_review: bool
    review_reason: Optional[str]
    review_id: Optional[int]
    approved_response: Optional[str]

    # Status Tracking
    status: str
    final_response: Optional[str]
    response_sent: bool
    followup_scheduled: bool

    # Metadata
    error_message: Optional[str]
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
