"""FastAPI application setup with lifespan management."""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from src.db.base import init_db
from src.graph.workflow import create_workflow
from src.graph.nodes_factory import get_all_nodes
from src.api.schemas import HealthResponse
from src.api.routes import emails, reviews

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — init DB and workflow on startup."""
    logger.info("🚀 Starting Customer Support Email Agent...")

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Build LangGraph workflow
    nodes = get_all_nodes()
    app.state.workflow = create_workflow(nodes)
    logger.info("✅ LangGraph workflow compiled with 10 nodes")

    logger.info("✅ Application ready!")
    logger.info("🌐 Dashboard at: http://localhost:8000")
    logger.info("📖 API docs at: http://localhost:8000/docs")

    yield

    logger.info("👋 Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Customer Support Email Agent",
        description=(
            "An Agentic AI system that processes customer emails end-to-end "
            "using a 10-node LangGraph pipeline with FAISS vector search, "
            "LLM-based classification, response generation, human-in-the-loop "
            "review, and automated follow-up scheduling."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    static_dir = os.path.join(BASE_DIR, "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Include API routers
    app.include_router(emails.router)
    app.include_router(reviews.router)

    @app.get("/", tags=["frontend"])
    async def serve_frontend():
        """Serve the frontend dashboard."""
        return FileResponse(os.path.join(static_dir, "index.html"))

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health_check():
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

    return app
