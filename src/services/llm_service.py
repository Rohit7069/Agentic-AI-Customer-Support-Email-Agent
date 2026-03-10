"""LLM service for email classification and response generation using OpenAI."""
import json
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import settings
from src.services.base import BaseService
from src.prompts.templates import (
    SYSTEM_PROMPT_CUSTOMER_SUPPORT,
    EMAIL_CLASSIFICATION_PROMPT,
    PRIORITY_ASSESSMENT_PROMPT,
    RESPONSE_GENERATION_PROMPT,
)

logger = logging.getLogger(__name__)


class LLMService(BaseService):
    """LangChain-wrapped OpenAI service for classification and response generation."""

    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )

    async def classify_email(self, subject: str, body: str) -> Dict[str, Any]:
        """Classify email into a category using the LLM."""
        try:
            prompt = EMAIL_CLASSIFICATION_PROMPT.format(
                subject=subject,
                email_body=body
            )

            messages = [
                SystemMessage(content=SYSTEM_PROMPT_CUSTOMER_SUPPORT),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(messages)
            category_raw = response.content.strip().lower()

            # Validate category
            valid_categories = [
                "product_inquiry", "billing", "technical_support",
                "complaint", "feedback", "other"
            ]
            category = category_raw if category_raw in valid_categories else "other"

            # Estimate confidence based on category match
            confidence = 0.9 if category_raw in valid_categories else 0.5

            return {
                "category": category,
                "confidence_score": confidence,
            }
        except Exception as e:
            logger.error(f"Email classification failed: {e}")
            return {
                "category": "other",
                "confidence_score": 0.0,
                "error": str(e),
            }

    async def assess_priority(self, body: str) -> Dict[str, Any]:
        """Assess email priority using the LLM."""
        try:
            prompt = PRIORITY_ASSESSMENT_PROMPT.format(email_body=body)

            messages = [
                SystemMessage(content=SYSTEM_PROMPT_CUSTOMER_SUPPORT),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(messages)
            priority_raw = response.content.strip().lower()
            
            valid_priorities = ["low", "medium", "high", "urgent"]
            priority = priority_raw if priority_raw in valid_priorities else "medium"

            return {"priority": priority}
        except Exception as e:
            logger.error(f"Priority assessment failed: {e}")
            return {"priority": "medium", "error": str(e)}

    async def generate_response(
        self, subject: str, body: str, category: str,
        priority: str, context: str = ""
    ) -> Dict[str, Any]:
        """Generate a customer support response."""
        try:
            context_section = ""
            if context:
                context_section = f"\nRelevant Knowledge Base Information:\n{context}"

            prompt = RESPONSE_GENERATION_PROMPT.format(
                classification=category,
                priority=priority,
                subject=subject,
                email_body=body,
                context=context_section,
            )

            messages = [
                SystemMessage(content=SYSTEM_PROMPT_CUSTOMER_SUPPORT),
                HumanMessage(content=prompt),
            ]

            # Use slightly higher temperature for response generation
            gen_llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.7
            )
            response = await gen_llm.ainvoke(messages)

            response_text = response.content.strip()
            
            # Extract token metadata if available
            tokens_used = 0
            if hasattr(response, 'response_metadata'):
                tokens_used = response.response_metadata.get('token_usage', {}).get('total_tokens', 0)

            return {
                "response_text": response_text,
                "model_used": settings.OPENAI_MODEL,
                "tokens_used": tokens_used,
            }
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return {
                "response_text": None,
                "error": str(e),
            }
