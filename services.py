from database import get_session
from sqlalchemy import select, func, and_, desc
from sqlalchemy.dialects.postgresql import insert as pg_insert
from models import Order, OrderDetail

def upsert_orders(orders):
    with get_session() as session:
        for order in orders:
            data = order.model_dump()
            existing = session.query(Order).filter_by(order_id=data["order_id"]).first()
            if existing:
                # update fields
                for key, value in data.items():
                    if value is not None:
                        setattr(existing, key, value)
            else:
                session.add(Order(**data))


def update_earnings(orders):
    with get_session() as session:
        for order in orders:
            data = order.model_dump()
            existing = session.query(Order).filter_by(order_id=data["order_id"]).first()
            if existing:
                # update fields
                for key, value in data.items():
                    if value is not None:
                        setattr(existing, key, value)




def get_orders(from_date:None, to_date:None):
    with get_session() as session:
        stmt = (
            select(
                Order.order_id,
                Order.cost_of_sales,
                Order.status,
                func.date(Order.shipped_time),
                Order.planned_earning,
                Order.earning,
                func.date(Order.settled_time),
            )
        )
                # apply filters if provided
        if from_date and to_date:
            stmt = stmt.where(
                and_(
                    Order.shipped_time >= from_date,
                    Order.shipped_time <= to_date
                )
            )
        elif from_date:
            stmt = stmt.where(Order.shipped_time >= from_date)
        elif to_date:
            stmt = stmt.where(Order.shipped_time <= to_date)

        result = session.execute(stmt).all()

        return [dict(row._mapping) for row in result]
    

def get_order_summary(session, from_date=None, to_date=None):
    query = (
        session.query(
            func.to_char(Order.shipped_time, 'YYYYMMDD').label("shipped_date"),
            func.count(Order.order_id).label("count"),
            func.sum(Order.cost_of_sales).label("cost_of_sales"),
            func.sum(Order.planned_earning).label("planned_earning"),
            func.sum(Order.earning - Order.cost_of_sales).label("earning"),
        )
        .group_by(func.to_char(Order.shipped_time, 'YYYYMMDD'))
        .order_by(func.to_char(Order.shipped_time, 'YYYYMMDD').desc())
    )

    if from_date and to_date:
        query = query.filter(Order.shipped_time.between(from_date, to_date))
    elif from_date:
        query = query.filter(Order.shipped_time >= from_date)
    elif to_date:
        query = query.filter(Order.shipped_time <= to_date)

    return query.all()


def upsert_order_details(order_details):
    if not order_details:
        return

    with get_session() as session:
        rows = [d.model_dump() for d in order_details]
        stmt = pg_insert(OrderDetail).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["order_id", "seller_sku"],
            set_={"qty": stmt.excluded.qty},
        )
        session.execute(stmt)