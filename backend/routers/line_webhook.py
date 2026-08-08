import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, UnfollowEvent
from sqlmodel import Session, select

from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from database import get_session
from models import LineSubscriber

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/line", tags=["line"])

_handler = WebhookHandler(LINE_CHANNEL_SECRET) if LINE_CHANNEL_SECRET else None
_line_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) if LINE_CHANNEL_ACCESS_TOKEN else None


@router.post("/webhook")
async def line_webhook(request: Request, session: Session = Depends(get_session)):
    if not _handler:
        raise HTTPException(status_code=503, detail="LINE not configured")

    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()

    try:
        _handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    return {"status": "ok"}


if _handler:
    @_handler.add(FollowEvent)
    def _on_follow(event):
        from database import engine
        with Session(engine) as session:
            line_user_id = event.source.user_id
            existing = session.exec(
                select(LineSubscriber).where(LineSubscriber.line_user_id == line_user_id)
            ).first()
            if not existing:
                display_name = None
                try:
                    if _line_api:
                        profile = _line_api.get_profile(line_user_id)
                        display_name = profile.display_name
                except Exception:
                    pass
                subscriber = LineSubscriber(line_user_id=line_user_id, display_name=display_name)
                session.add(subscriber)
                session.commit()
                logger.info(f"LINE subscriber added: {line_user_id} ({display_name})")

    @_handler.add(UnfollowEvent)
    def _on_unfollow(event):
        from database import engine
        with Session(engine) as session:
            line_user_id = event.source.user_id
            subscriber = session.exec(
                select(LineSubscriber).where(LineSubscriber.line_user_id == line_user_id)
            ).first()
            if subscriber:
                session.delete(subscriber)
                session.commit()
                logger.info(f"LINE subscriber removed: {line_user_id}")
