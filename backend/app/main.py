from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deals import router as deals_router
from app.api.health import router as health_router
from app.api.search import router as search_router
from app.api.stats import router as stats_router
from app.core.config import settings

app = FastAPI(title="sizehive")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(deals_router, prefix="/api")
