import logging
from datetime import datetime

import pytz
import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

from config import POLL_INTERVAL_MINUTES
from database import engine
from models import Alert, LineSubscriber
from notifier import send_email, send_line

logger = logging.getLogger(__name__)
TZ_TAIPEI = pytz.timezone("Asia/Taipei")
scheduler = BackgroundScheduler()


def _is_market_open() -> bool:
    now = datetime.now(TZ_TAIPEI)
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=13, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


def check_alerts() -> None:
    if not _is_market_open():
        return
    try:
        with Session(engine) as session:
            all_alerts = session.exec(select(Alert)).all()
            if not all_alerts:
                return

            tickers = list({a.ticker for a in all_alerts})
            data = yf.download(tickers, period="1d", interval="5m", progress=False)

            subscriber_ids = [
                s.line_user_id for s in session.exec(select(LineSubscriber)).all()
            ]

            for alert in all_alerts:
                try:
                    close = data["Close"]
                    prices = close[alert.ticker] if alert.ticker in close.columns else close.iloc[:, 0]
                    current_price = float(prices.dropna().iloc[-1])
                    now = datetime.utcnow()
                    changed = False

                    if alert.above_price is not None:
                        if current_price >= alert.above_price:
                            if alert.above_triggered_at is None:
                                alert.above_triggered_at = now
                                changed = True
                                send_email(alert, "above", alert.above_price, current_price)
                            send_line(alert, "above", alert.above_price, current_price, subscriber_ids)

                    if alert.equal_price is not None:
                        if abs(current_price - alert.equal_price) / alert.equal_price <= 0.005:
                            if alert.equal_triggered_at is None:
                                alert.equal_triggered_at = now
                                changed = True
                                send_email(alert, "equal", alert.equal_price, current_price)
                            send_line(alert, "equal", alert.equal_price, current_price, subscriber_ids)

                    if alert.below_price is not None:
                        if current_price <= alert.below_price:
                            if alert.below_triggered_at is None:
                                alert.below_triggered_at = now
                                changed = True
                                send_email(alert, "below", alert.below_price, current_price)
                            send_line(alert, "below", alert.below_price, current_price, subscriber_ids)

                    if changed:
                        session.add(alert)
                        session.commit()

                except Exception as e:
                    logger.error(f"Error processing alert {alert.id}: {e}")

    except Exception as e:
        logger.error(f"check_alerts failed: {e}")


def start_scheduler() -> None:
    scheduler.add_job(check_alerts, "interval", minutes=POLL_INTERVAL_MINUTES)
    scheduler.start()
    logger.info(f"Scheduler started, polling every {POLL_INTERVAL_MINUTES} minute(s)")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
