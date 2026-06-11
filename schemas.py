from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# --- Common base schema ---
class OrderBase(BaseModel):
    order_id: Optional[str] = Field(None, max_length=100)
    channel: Optional[str] = Field(default="tts", max_length=3)
    status: Optional[str] = Field(default="In transit", max_length=30)
    cost_of_sales: Optional[float] = None
    after_discount_amount: Optional[float] = None
    platform_fee: Optional[float] = None
    tax_and_fee: Optional[float] = None
    earning: Optional[float] = None
    planned_earning: Optional[float] = None
    shipped_time: Optional[datetime] = None
    delivered_time: Optional[datetime] = None
    settled_time: Optional[datetime] = None

    # shared validators
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"In transit", "Delivered", "Cancelled"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"tts", "sp", "laz"}
        if v not in allowed:
            raise ValueError(f"channel must be one of {allowed}")
        return v


# --- Create Schema (for inserts, strict) ---
class OrderCreate(OrderBase):
    order_id: str
    cost_of_sales: float
    after_discount_amount: float
    shipped_time: datetime


# --- Update Schema (for updates, relaxed) ---
class OrderUpdate(OrderBase):
    """
    All fields optional.
    Only used when partially updating an existing record.
    Example: updating earning or settled_time after settlement.
    """
    pass


class OrderDetailCreate(BaseModel):
    order_id:   str = Field(..., max_length=100)
    seller_sku: str = Field(..., max_length=100)
    qty:        int = Field(..., ge=1)