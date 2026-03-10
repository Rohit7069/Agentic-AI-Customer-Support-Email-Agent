"""SQLAlchemy ORM models for the email agent system."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from src.db.base import Base
from src.db.enums import (
    EmailStatusEnum, EmailPriorityEnum, ReviewStatusEnum,
    ReviewReasonEnum, FollowUpTypeEnum
)


class Customer(Base):
    """Customer record."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    emails = relationship("Email", back_populates="customer", lazy="selectin")


class Email(Base):
    """Incoming customer email with classification and status tracking."""
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    sender = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    html_body = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    priority = Column(SAEnum(EmailPriorityEnum), nullable=True)
    confidence_score = Column(Float, nullable=True)
    status = Column(SAEnum(EmailStatusEnum), default=EmailStatusEnum.PENDING)
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="emails")
    responses = relationship("EmailResponse", back_populates="email", lazy="selectin")
    reviews = relationship("HumanReview", back_populates="email", lazy="selectin")
    followups = relationship("FollowUp", back_populates="email", lazy="selectin")


class EmailResponse(Base):
    """AI-generated response with model metadata."""
    __tablename__ = "email_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    response_text = Column(Text, nullable=False)
    response_subject = Column(String(500), nullable=True)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0)
    requires_review = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    email = relationship("Email", back_populates="responses")


class HumanReview(Base):
    """Review task for escalated emails."""
    __tablename__ = "human_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    reason = Column(SAEnum(ReviewReasonEnum), nullable=True)
    review_reason_text = Column(Text, nullable=True)
    status = Column(SAEnum(ReviewStatusEnum), default=ReviewStatusEnum.PENDING)
    original_response = Column(Text, nullable=True)
    approved_response = Column(Text, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    email = relationship("Email", back_populates="reviews")


class FollowUp(Base):
    """Scheduled follow-up actions."""
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    followup_type = Column(SAEnum(FollowUpTypeEnum), nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    status = Column(String(50), default="pending")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    email = relationship("Email", back_populates="followups")
