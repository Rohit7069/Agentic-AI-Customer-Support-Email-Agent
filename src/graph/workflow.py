"""LangGraph workflow definition — connects all 10 nodes."""
from typing import Literal
from langgraph.graph import StateGraph, END
from src.graph.state import EmailAgentState


def create_workflow(nodes: dict):
    """Create the email processing workflow.

    Args:
        nodes: Dictionary mapping node names to async functions.

    Returns:
        Compiled LangGraph workflow.
    """
    workflow = StateGraph(EmailAgentState)

    # Add all nodes
    workflow.add_node("email_retrieval", nodes["email_retrieval"])
    workflow.add_node("guardrails", nodes["guardrails"])
    workflow.add_node("classification", nodes["classification"])
    workflow.add_node("context_analysis", nodes["context_analysis"])
    workflow.add_node("review_check", nodes["review_check"])
    workflow.add_node("response_generation", nodes["response_generation"])
    workflow.add_node("review_routing", nodes["review_routing"])
    workflow.add_node("human_review", nodes["human_review"])
    workflow.add_node("response_sending", nodes["response_sending"])
    workflow.add_node("followup_scheduling", nodes["followup_scheduling"])
    workflow.add_node("error_handler", nodes["error_handler"])

    # Set entry point
    workflow.set_entry_point("email_retrieval")

    # Define edges
    def route_after_retrieval(state) -> Literal["guardrails", "error_handler"]:
        if state.get("error_message"):
            return "error_handler"
        return "guardrails"

    workflow.add_conditional_edges("email_retrieval", route_after_retrieval)

    def route_after_guardrails(state) -> Literal["classification", "error_handler", "review_routing"]:
        if state.get("error_message"):
            return "error_handler"
        if state.get("needs_human_review"):
            # If safety flagged, skip to review routing
            return "review_routing"
        return "classification"

    workflow.add_conditional_edges("guardrails", route_after_guardrails)

    workflow.add_conditional_edges(
        "classification",
        lambda state: "context_analysis" if not state.get("error_message") else "error_handler",
    )

    workflow.add_edge("context_analysis", "review_check")
    workflow.add_edge("review_check", "response_generation")

    # Conditional routing after response generation
    def route_after_generation(state) -> Literal[
        "review_routing", "response_sending", "error_handler"
    ]:
        if state.get("error_message"):
            return "error_handler"
        if state.get("needs_human_review"):
            return "review_routing"
        return "response_sending"

    workflow.add_conditional_edges(
        "response_generation",
        route_after_generation,
    )

    # Halt the graph after creating the review record
    workflow.add_edge("review_routing", END)

    # Link human_review to response_sending (for when we resume)
    workflow.add_edge("human_review", "response_sending")

    workflow.add_conditional_edges(
        "response_sending",
        lambda state: "followup_scheduling" if state.get("status") == "responded" else "error_handler",
    )

    workflow.add_edge("followup_scheduling", END)
    workflow.add_edge("error_handler", END)

    return workflow.compile()
