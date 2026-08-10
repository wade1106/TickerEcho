import logging
import smtplib
from email.mime.text import MIMEText

from config import (
    LINE_CHANNEL_ACCESS_TOKEN,
    MAIL_FROM, MAIL_PASSWORD, MAIL_PORT, MAIL_SERVER, MAIL_USERNAME,
)
from models import Alert

logger = logging.getLogger(__name__)
_LABELS = {"above": "高於", "equal": "等於（±0.5%）", "below": "低於"}


def _build_message(alert: Alert, condition: str, target_price: float, current_price: float) -> str:
    return (
        f"【TickerEcho 股價警報】\n"
        f"股票：{alert.name}（{alert.ticker}）\n"
        f"條件：{_LABELS.get(condition, condition)} {target_price}\n"
        f"當前價格：{current_price}\n"
    )


def send_email(alert: Alert, condition: str, target_price: float, current_price: float) -> None:
    if not alert.user_email or not (MAIL_USERNAME and MAIL_PASSWORD and MAIL_SERVER):
        return
    try:
        msg = MIMEText(_build_message(alert, condition, target_price, current_price), "plain", "utf-8")
        msg["Subject"] = f"【TickerEcho】{alert.name} {_LABELS.get(condition)} {target_price}"
        msg["From"] = MAIL_FROM
        msg["To"] = alert.user_email
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as smtp:
            smtp.ehlo(); smtp.starttls()
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.sendmail(MAIL_FROM, [alert.user_email], msg.as_string())
        logger.info(f"Email sent: alert={alert.id} {condition} {target_price}")
    except Exception as e:
        logger.error(f"Email failed alert={alert.id}: {e}")


def send_line(alert: Alert, condition: str, target_price: float, current_price: float, subscriber_ids: list[str]) -> None:
    if not LINE_CHANNEL_ACCESS_TOKEN or not subscriber_ids:
        return
    from linebot import LineBotApi
    from linebot.models import TextSendMessage
    api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    msg = TextSendMessage(text=_build_message(alert, condition, target_price, current_price))
    for uid in subscriber_ids:
        try:
            api.push_message(uid, msg)
            logger.info(f"LINE sent: alert={alert.id} {condition} {target_price} -> {uid}")
        except Exception as e:
            logger.error(f"LINE failed alert={alert.id} -> {uid}: {e}")
