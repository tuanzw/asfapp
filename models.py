from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, inspect, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    channel: Mapped[str] = mapped_column(String(3), nullable=False, default="tts")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="In transit")
    cost_of_sales: Mapped[float] = mapped_column(Float, nullable=False)
    after_discount_amount: Mapped[float] = mapped_column(Float, nullable=False)
    platform_fee: Mapped[float | None] = mapped_column(Float, nullable=True)
    tax_and_fee: Mapped[float | None] = mapped_column(Float, nullable=True)
    earning: Mapped[float | None] = mapped_column(Float, nullable=False, default=0.0)
    planned_earning: Mapped[float | None] = mapped_column(Float, nullable=True)
    shipped_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    delivered_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    settled_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Check if this is a new object (not loaded from DB)
        is_new = not hasattr(self, "_sa_instance_state") or self._sa_instance_state.transient

        if is_new:
            # Dynamically find required fields (nullable=False, not primary key, no default)
            mapper = inspect(self.__class__)
            required_fields = [
                col.key
                for col in mapper.columns
                if not col.nullable and not col.primary_key and col.default is None
            ]

            # Check which required fields are missing in constructor args
            missing = [f for f in required_fields if f not in kwargs or kwargs[f] is None]
            if missing:
                raise ValueError(f"Missing required fields for new Order: {', '.join(missing)}")

            # Compute auto fields
            after_discount = kwargs.get("after_discount_amount")
            cost_of_sales = kwargs.get("cost_of_sales")

            if after_discount is not None and cost_of_sales is not None:
                self.tax_and_fee = after_discount * 1.5 / 100
                if not kwargs.get("platform_fee"):
                    self.platform_fee = after_discount * 16.5 / 100
                self.planned_earning = (
                    after_discount
                    - cost_of_sales
                    - self.platform_fee
                    - self.tax_and_fee
                )
            if self.channel == 'tts': self.planned_earning = self.planned_earning - 3000
    

    def __repr__(self):
        return f"<Order(order_id={self.order_id}, status={self.status}, earning={self.earning})>"

class OrderDetail(Base):
    __tablename__ = "order_details"

    order_id:   Mapped[str] = mapped_column(String(100), nullable=False)
    seller_sku: Mapped[str] = mapped_column(String(100), nullable=False)
    qty:        Mapped[int] = mapped_column(Integer,     nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("order_id", "seller_sku"),
    )