"""Context analysis node — gathers customer history and searches knowledge base."""
import logging
from src.graph.state import EmailAgentState
from src.services.database_service import DatabaseService
from src.services.vector_kb_service import VectorKBService

logger = logging.getLogger(__name__)


async def context_analysis_node(state: EmailAgentState) -> dict:
    """Gather customer history and search knowledge base."""
    try:
        customer_id = state.get("customer_id")
        subject = state.get("subject", "")
        body = state.get("body", "")
        category = state.get("category", "other")

        db_service = DatabaseService()
        vector_kb = VectorKBService()
        await vector_kb.initialize()

        # Get customer history from database
        customer_history = []
        if customer_id:
            history_emails = await db_service.get_customer_emails(
                customer_id, limit=5
            )
            customer_history = [
                {
                    "date": str(email.received_at),
                    "subject": email.subject,
                    "category": email.category,
                    "status": email.status.value if email.status else "unknown",
                }
                for email in history_emails
            ]

        # Semantic search using FAISS + OpenAI embeddings
        search_query = f"{subject} {body[:200]}"
        kb_results = await vector_kb.search(
            search_query,
            category=category,
            limit=5,
            threshold=0.3,
        )

        # Format for LLM consumption
        context_summary = await vector_kb.format_context(kb_results)

        logger.info(
            f"Context analysis for email {state.get('email_id')}: "
            f"{len(kb_results)} KB results, {len(customer_history)} history items"
        )

        return {
            "customer_history": customer_history,
            "kb_results": kb_results,
            "context_summary": context_summary,
        }

    except Exception as e:
        logger.error(f"Context analysis failed: {e}")
        return {
            "customer_history": [],
            "kb_results": [],
            "context_summary": "No additional context available.",
        }
