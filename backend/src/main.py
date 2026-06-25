"""Main FastAPI application using pycore APIServer."""

from pycore.api import APIConfig, APIServer
from pycore.api.responses import success_response
from pycore.core import Logger, LoggerConfig, LogLevel, get_logger
from src.api.routes import auth, conversations, kb, tickets, ws
from src.core.config import settings

# Configure logger
Logger.configure(
    LoggerConfig(
        level=LogLevel.INFO,
        app_name="customer-service",
        json_format=False,
    )
)
logger = get_logger()

# Create API server
server = APIServer(
    APIConfig(
        title="智能客服系统 API",
        description="基于百炼大模型的智能客服系统后端",
        version="1.0.0",
        host="127.0.0.1",
        port=settings.api_port,
        debug=True,
        cors_origins=settings.cors_origins,
    )
)


async def startup_handler() -> None:
    """Application startup handler."""
    logger.info("Starting customer service application", port=settings.api_port)
    # Ensure data directory exists
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Data directory ready", path=str(settings.data_dir))


async def shutdown_handler() -> None:
    """Application shutdown handler."""
    logger.info("Shutting down customer service application")


# Register lifecycle handlers
server.on_startup(startup_handler)
server.on_shutdown(shutdown_handler)

# Register routes
server.include_router(auth.router)
server.include_router(conversations.router)
server.include_router(kb.router)
server.include_router(tickets.router)
server.include_router(ws.router)

# FastAPI app instance
app = server.app

# Replace pycore default /health (status: healthy) with api-contracts format
for i, route in enumerate(app.router.routes):
    if getattr(route, "path", None) == "/health":
        del app.router.routes[i]
        break


@app.get("/health")
async def health_check():  # type: ignore[no-untyped-def]
    """Health check endpoint per api-contracts (status: ok)."""
    return success_response({"status": "ok"})

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=settings.api_port,
        reload=True,
    )
