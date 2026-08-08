import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import check_notification_channels
from database import init_db
from routers import alerts, auth, line_webhook, stocks
from scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. DB migration (must be first)
    init_db()
    logger.info("Database initialized")

    # 2. Check notification channels
    check_notification_channels()

    # 3. Start scheduler
    start_scheduler()

    yield

    # Shutdown
    stop_scheduler()


app = FastAPI(title="TickerEcho", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(alerts.router)
app.include_router(stocks.router)
app.include_router(line_webhook.router)

# Serve Vue static files (must be last)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
