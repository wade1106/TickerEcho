from datetime import datetime, date
from typing import Optional
from sqlmodel import Field, SQLModel


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(nullable=False, index=True)  # no unique — multiple rows per stock allowed
    name: str = Field(nullable=False)
    user_email: str = Field(default="", nullable=False)

    above_price: Optional[float] = Field(default=None)
    equal_price: Optional[float] = Field(default=None)
    below_price: Optional[float] = Field(default=None)

    above_triggered_at: Optional[datetime] = Field(default=None)
    equal_triggered_at: Optional[datetime] = Field(default=None)
    below_triggered_at: Optional[datetime] = Field(default=None)

    # LINE edge-trigger tracking: True = condition was met in previous poll
    above_line_active: bool = Field(default=False)
    equal_line_active: bool = Field(default=False)
    below_line_active: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class LineSubscriber(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    line_user_id: str = Field(nullable=False, unique=True)
    display_name: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InvestmentPlan(SQLModel, table=True):
    __tablename__ = "investment_plan"

    id: Optional[int] = Field(default=None, primary_key=True)
    plan_date: date = Field(nullable=False, index=True)
    plan_name: str = Field(nullable=False)
    investor: str = Field(nullable=False, index=True)
    ticker: str = Field(nullable=False, index=True)
    stock_name: str = Field(default="", nullable=False)
    content: str = Field(default="", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
