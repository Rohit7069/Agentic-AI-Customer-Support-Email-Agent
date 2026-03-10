"""Response generation node — generates AI response with retry logic."""
import logging
from src.graph.state import EmailAgentState
from src.services.llm_service import LLMService
from src.services.database_service import DatabaseService

logger = logging.getLogger(__name__)


async def response_generation_node(state: EmailAgentState) -> dict:
    """Generate response with retry logic."""
    try:
        response_attempt = state.get("response_attempt", 0)
        llm_service = LLMService()

        response_result = await llm_service.generate_response(
            subject=state.get("subject", ""),
            body=state.get("body", ""),
            category=state.get("category", "other"),
            priority=state.get("priority", "medium"),
            context=state.get("context_summary", ""),
        )

        response_text = response_result.get("response_text")
        error = response_result.get("error")

        if error or not response_text or len(response_text) < 50:
            if response_attempt < 2:
                logger.warning(
                    f"Response attempt {response_attempt + 1} failed for "
                    f"email {state.get('email_id')}, retrying..."
                )
                return {"response_attempt": response_attempt + 1}

            logger.error(
                f"Response generation failed after 3 attempts for "
                f"email {state.get('email_id')}"
            )
            return {
                "error_message": "Response generation failed after 3 attempts",
                "needs_human_review": True,
                "review_reason": "Response generation failed",
            }

        # Save response to database
        db_service = DatabaseService()
        await db_service.create_response(
            email_id=state.get("email_id"),
            response_text=response_text,
            response_subject=f"Re: {state.get('subject', '')}",
            model_used=response_result.get("model_used"),
            tokens_used=response_result.get("tokens_used", 0),
            requires_review=state.get("needs_human_review", False),
        )

        logger.info(
            f"Generated response for email {state.get('email_id')} "
            f"(attempt {response_attempt + 1})"
        )

        return {
            "generated_response": response_text,
            "response_subject": f"Re: {state.get('subject', '')}",
            "model_used": response_result.get("model_used"),
            "tokens_used": response_result.get("tokens_used", 0),
            "response_attempt": response_attempt + 1,
        }

    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return {
            "error_message": f"Response generation failed: {str(e)}",
            "needs_human_review": True,
            "review_reason": "Response generation failed",
        }
