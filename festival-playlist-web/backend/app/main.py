import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import lineup, poster, youtube


load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)


def create_app():
    app = FastAPI(title="Festival Playlist Web API")

    default_origins = "http://localhost:5173,http://127.0.0.1:5173"
    origins = os.getenv("FRONTEND_ORIGINS", default_origins).split(",")
    origins = [origin.strip() for origin in origins if origin.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(poster.router, prefix="/api/poster", tags=["poster"])
    app.include_router(lineup.router, prefix="/api/lineup", tags=["lineup"])
    app.include_router(youtube.router, prefix="/api/youtube", tags=["youtube"])

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    logger.info("FastAPI app initialized")
    return app


app = create_app()
