import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import check_notification_channels
from database import init_db
from routers import alerts, auth, investment_plans, line_webhook, stocks
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
app.include_router(investment_plans.router)

# Serve Vue static files (must be last)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    # Serve actual static assets (js/css/images) directly
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    # SPA catch-all: serve index.html for any non-API route (supports Vue Router history mode)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file = static_dir / full_path
        if file.exists() and file.is_file():
            return FileResponse(str(file))
        return FileResponse(str(static_dir / "index.html"))
