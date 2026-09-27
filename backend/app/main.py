"""
Price Intelligence Dashboard — FastAPI Application.
Main entry point for the backend.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api.search import router as search_router
from app.api.products import router as products_router
from app.api.tracking import router as tracking_router
from app.schemas.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Demo mode: {settings.is_demo_mode}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize History Registry
    from app.history.registry import history_registry
    from app.history.own_database import OwnDatabaseProvider
    from app.database import async_session
    
    own_db_provider = OwnDatabaseProvider(async_session)
    history_registry.register(own_db_provider)
    history_registry.set_fallback(own_db_provider)
    
    # Add Keepa first for Amazon if configured
    if settings.KEEPA_API_KEY:
        from app.history.keepa import KeepaProvider
        keepa_provider = KeepaProvider()
        keepa_provider.priority = 10
        history_registry.register(keepa_provider)
        
    logger.info("History registry initialized")

    # Initialize Adapter Registry
    from app.adapters.registry import adapter_registry
    from app.adapters.generic import GenericAdapter
    adapter_registry.set_fallback(GenericAdapter())
    logger.info("Adapter registry initialized")
    
    # Start background worker
    from app.workers import PriceTracker
    app.state.tracker = PriceTracker()
    await app.state.tracker.start()

    yield

    # Shutdown
    logger.info("Shutting down...")
    await app.state.tracker.stop()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Unified E-commerce Price Intelligence & Historical Price Dashboard",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router)
app.include_router(products_router)
app.include_router(tracking_router)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    history_provider = "demo" if settings.is_demo_mode else "own_database"
    if settings.KEEPA_API_KEY and not settings.is_demo_mode:
        history_provider = "keepa+own_database"
        
    providers = {
        "search": "serper" if settings.SERPER_API_KEY else "demo",
        "llm": "gemini" if settings.GEMINI_API_KEY else "rule-based",
        "history": history_provider,
    }

    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        demo_mode=settings.is_demo_mode,
        providers=providers,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
