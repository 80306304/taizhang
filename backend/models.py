from pydantic import BaseModel
from typing import Optional


class RecordCreate(BaseModel):
    customer: str = ""
    product: str = ""
    cost_price: float = 0
    buy_price: float = 0
    other_income: float = 0
    actual_profit: float = 0
    tracking_no: str = ""
    tracking_company: str = ""
    is_returned: int = 0
    returned_at: Optional[str] = None
    note: str = ""
    raw_input: str = ""


class RecordUpdate(BaseModel):
    customer: Optional[str] = None
    product: Optional[str] = None
    cost_price: Optional[float] = None
    buy_price: Optional[float] = None
    other_income: Optional[float] = None
    actual_profit: Optional[float] = None
    tracking_no: Optional[str] = None
    tracking_company: Optional[str] = None
    is_returned: Optional[int] = None
    returned_at: Optional[str] = None
    note: Optional[str] = None


class ParseRequest(BaseModel):
    text: str


class StatsResponse(BaseModel):
    total_orders: int
    total_cost: float
    total_profit: float
    returned_count: int
    unreturned_count: int
    return_rate: float
    total_buy_price: float


class TrackingStatus(BaseModel):
    tracking_state: str = ""
    tracking_state_text: str = "未查询"
    tracking_latest_time: str = ""
    tracking_latest_context: str = ""
    tracking_updated_at: Optional[str] = None
