"""Enum definitions for database models."""
import enum


class EmailStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    CLASSIFIED = "classified"
    RESPONDED = "responded"
    REVIEW_PENDING = "review_pending"
    REVIEW_APPROVED = "review_approved"
    SENT = "sent"
    FAILED = "failed"
    COMPLETED = "completed"


class EmailPriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ReviewStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class ReviewReasonEnum(str, enum.Enum):
    LOW_CONFIDENCE = "low_confidence"
    ESCALATED_COMPLAINT = "escalated_complaint"
    CRITICAL_KEYWORDS = "critical_keywords"
    UNCERTAIN_CATEGORY = "uncertain_category"
    GENERATION_FAILED = "generation_failed"


class FollowUpTypeEnum(str, enum.Enum):
    CHECK_RESOLUTION = "check_resolution"
    SATISFACTION_SURVEY = "satisfaction_survey"
    ESCALATION_REVIEW = "escalation_review"
    BILLING_CONFIRMATION = "billing_confirmation"
    FEEDBACK_ACKNOWLEDGMENT = "feedback_acknowledgment"
