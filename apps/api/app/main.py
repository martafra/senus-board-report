from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, insights, metrics, targets

settings = get_settings()

app = FastAPI(
    title="Senus PLC Board Report API",
    version="0.1.0",
    description="Backend powering the Senus PLC AI-native Board Report platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(metrics.router)
app.include_router(insights.router)
app.include_router(targets.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
