from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlmodel import Session, select

from auth import get_current_user
from database import get_session
from models import Alert

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    ticker: str
    name: str
    user_email: str = ""
    above_price: Optional[float] = None
    equal_price: Optional[float] = None
    below_price: Optional[float] = None


class AlertUpdate(BaseModel):
    user_email: Optional[str] = None
    above_price: Optional[float] = None
    equal_price: Optional[float] = None
    below_price: Optional[float] = None


def _is_active(a: Alert) -> bool:
    return (
        (a.above_price is not None and a.above_triggered_at is None)
        or (a.equal_price is not None and a.equal_triggered_at is None)
        or (a.below_price is not None and a.below_triggered_at is None)
    )


def _alert_dict(a: Alert) -> dict:
    return {
        "id": a.id,
        "ticker": a.ticker,
        "name": a.name,
        "user_email": a.user_email,
        "above_price": a.above_price,
        "equal_price": a.equal_price,
        "below_price": a.below_price,
        "above_triggered_at": a.above_triggered_at,
        "equal_triggered_at": a.equal_triggered_at,
        "below_triggered_at": a.below_triggered_at,
        "is_active": _is_active(a),
        "created_at": a.created_at,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_alert(
    body: AlertCreate,
    session: Session = Depends(get_session),
    _: str = Depends(get_current_user),
):
    if body.above_price is None and body.equal_price is None and body.below_price is None:
        raise HTTPException(status_code=400, detail="至少需要設定一個條件價格")

    # Reject exact duplicate (same ticker + same prices + still active)
    existing = session.exec(
        select(Alert).where(
            Alert.ticker == body.ticker,
            Alert.above_price == body.above_price,
            Alert.equal_price == body.equal_price,
            Alert.below_price == body.below_price,
        )
    ).first()
    if existing and _is_active(existing):
        raise HTTPException(status_code=409, detail="已有完全相同條件的警報在監控中")

    alert = Alert(
        ticker=body.ticker,
        name=body.name,
        user_email=body.user_email,
        above_price=body.above_price,
        equal_price=body.equal_price,
        below_price=body.below_price,
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return _alert_dict(alert)


@router.get("")
def list_alerts(
    session: Session = Depends(get_session),
    _: str = Depends(get_current_user),
):
    alerts = session.exec(select(Alert).order_by(Alert.created_at.desc())).all()
    return [_alert_dict(a) for a in alerts]


@router.patch("/{alert_id}", status_code=status.HTTP_200_OK)
def update_alert(
    alert_id: int,
    body: AlertUpdate,
    session: Session = Depends(get_session),
    _: str = Depends(get_current_user),
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if body.user_email is not None:
        alert.user_email = body.user_email
    # Reset triggered_at if price changes
    if body.above_price != alert.above_price:
        alert.above_price = body.above_price
        alert.above_triggered_at = None
    if body.equal_price != alert.equal_price:
        alert.equal_price = body.equal_price
        alert.equal_triggered_at = None
    if body.below_price != alert.below_price:
        alert.below_price = body.below_price
        alert.below_triggered_at = None

    session.commit()
    session.refresh(alert)
    return _alert_dict(alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    session: Session = Depends(get_session),
    _: str = Depends(get_current_user),
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    session.delete(alert)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
