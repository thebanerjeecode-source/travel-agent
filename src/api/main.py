from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import get_allowed_origins
from src.api.routes.plans import router as plans_router
from src.api.schemas import HealthResponse

load_dotenv()

app = FastAPI(
    title="AI Travel Planner API",
    description="Multi-agent trip planning — wraps the existing Orchestrator pipeline.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plans_router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {
        "service": "AI Travel Planner API",
        "docs": "/docs",
        "health": "/health",
    }


def main() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=os.getenv("RELOAD") == "1")


if __name__ == "__main__":
    main()
