from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlmodel import Session, select

from auth import get_current_user
from database import get_session
from models import InvestmentPlan

router = APIRouter(prefix="/api/investment-plans", tags=["investment-plans"])


VALID_URGENCY = {"immediate", "waiting", "watching", "note"}
VALID_STATUS  = {"draft", "pending", "active", "done", "cancelled"}


class PlanCreate(BaseModel):
    plan_date: date
    plan_name: str
    investor: str
    ticker: str
    stock_name: str = ""
    content: str = ""
    urgency: str = "note"
    status: str = "draft"
    trigger_above: Optional[float] = None
    trigger_equal: Optional[float] = None
    trigger_below: Optional[float] = None
    linked_alert_id: Optional[int] = None


class PlanUpdate(BaseModel):
    plan_date: Optional[date] = None
    plan_name: Optional[str] = None
    investor: Optional[str] = None
    ticker: Optional[str] = None
    stock_name: Optional[str] = None
    content: Optional[str] = None
    urgency: Optional[str] = None
    status: Optional[str] = None
    trigger_above: Optional[float] = None
    trigger_equal: Optional[float] = None
    trigger_below: Optional[float] = None
    linked_alert_id: Optional[int] = None


def _plan_dict(p: InvestmentPlan) -> dict:
    return {
        "id": p.id,
        "plan_date": p.plan_date.isoformat() if p.plan_date else None,
        "plan_name": p.plan_name,
        "investor": p.investor,
        "ticker": p.ticker,
        "stock_name": p.stock_name,
        "content": p.content,
        "urgency": p.urgency,
        "status": p.status,
        "trigger_above": p.trigger_above,
        "trigger_equal": p.trigger_equal,
        "trigger_below": p.trigger_below,
        "linked_alert_id": p.linked_alert_id,
        "created_at": p.created_at,
    }


@router.get("")
def list_plans(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    plan_date: Optional[date] = None,
    stock: Optional[str] = None,
    investor: Optional[str] = None,
    urgency: Optional[str] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_session),
    _: str = Depends(get_current_user),
):
    conditions = []
    if plan_date:
        conditions.append(InvestmentPlan.plan_date == plan_date)
    if stock:
        conditions.append(
            or_(
                InvestmentPlan.ticker.contains(stock),
                InvestmentPlan.stock_name.contains(stock),
            )
        )
    if investor:
        conditions.append(InvestmentPlan.investor.contains(investor))
    if urgency and urgency in VALID_URGENCY:
        conditions.append(InvestmentPlan.urgency == urgency)
    if status and status in VALID_STATUS:
        conditions.append(InvestmentPlan.status == status)

    count_q = select(func.count(InvestmentPlan.id))
    for c in conditions:
        count_q = count_q.where(c)
    total = session.exec(count_q).one()

    items_q = select(InvestmentPlan)
    for c in conditions:
        items_q = items_q.where(c)
    items_q = items_q.order_by(InvestmentPlan.plan_date.desc(), InvestmentPlan.id.desc())
    items_q = items_q.offset((page - 1) * page_size).limit(page_size)
    items = session.exec(items_q).all()

    return {"items": [_plan_dict(p) for p in items], "total": total, "page": page, "page_size": page_size}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_plan(
    body: PlanCreate,
    session: Session = Depends(get_session),
    _: str = Depends(get_current_user),
):
    if body.urgency not in VALID_URGENCY:
        raise HTTPException(status_code=422, detail=f"Invalid urgency: {body.urgency}")
    if body.status not in VALID_STATUS:
        raise HTTPException(status_code=422, detail=f"Invalid status: {body.status}")
    plan = InvestmentPlan(**body.model_dump())
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return _plan_dict(plan)


@router.put("/{plan_id}")
def update_plan(
    plan_id: int,
    body: PlanUpdate,
    session: Session = Depends(get_session),
    _: str = Depends(get_current_user),
):
    plan = session.get(InvestmentPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Investment plan not found")
    data = body.model_dump(exclude_unset=True)
    if "urgency" in data and data["urgency"] not in VALID_URGENCY:
        raise HTTPException(status_code=422, detail=f"Invalid urgency: {data['urgency']}")
    if "status" in data and data["status"] not in VALID_STATUS:
        raise HTTPException(status_code=422, detail=f"Invalid status: {data['status']}")
    for field, val in data.items():
        setattr(plan, field, val)
    session.commit()
    session.refresh(plan)
    return _plan_dict(plan)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    session: Session = Depends(get_session),
    _: str = Depends(get_current_user),
):
    plan = session.get(InvestmentPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Investment plan not found")
    session.delete(plan)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
