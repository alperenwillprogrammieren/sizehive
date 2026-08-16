import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.account import router as account_router
from app.api.deals import router as deals_router
from app.api.health import router as health_router
from app.api.search import router as search_router
from app.api.stats import router as stats_router
from app.core.config import settings

# Nothing else configures logging, so the root logger would sit at WARNING
# and swallow INFO. That matters concretely: without SMTP configured, login
# links and notification bodies are written to the log instead of sent, and
# dev login would be impossible if those lines disappeared.
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

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
app.include_router(account_router, prefix="/api")
