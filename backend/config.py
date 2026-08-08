import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Auth
APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "changeme")
JWT_SECRET = os.getenv("JWT_SECRET", "insecure-default-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/tickerecho.db")

# Polling
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "5"))

# Email
MAIL_SERVER = os.getenv("MAIL_SERVER", "")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME)

# LINE
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")


def check_notification_channels() -> None:
    email_ready = bool(MAIL_USERNAME and MAIL_PASSWORD and MAIL_SERVER)
    line_ready = bool(LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET)

    if not email_ready:
        logger.warning(
            "Email notification disabled: MAIL_USERNAME, MAIL_PASSWORD or MAIL_SERVER not set."
        )
    if not line_ready:
        logger.warning(
            "LINE notification disabled: LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_SECRET not set."
        )
    if not email_ready and not line_ready:
        logger.warning(
            "No notification channels configured. Alerts will trigger but no notifications will be sent."
        )
