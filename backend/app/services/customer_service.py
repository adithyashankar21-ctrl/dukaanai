from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models import Customer, Shop


def search_customers(db: Session, shop_id: int, query: str | None = None, limit: int = 15) -> list[Customer]:
    q = db.query(Customer).filter(Customer.shop_id == shop_id)

    if query and query.strip():
        like = f"%{query.strip()}%"
        q = q.filter(or_(Customer.name.ilike(like), Customer.phone.ilike(like)))

    return q.order_by(Customer.id).limit(limit).all()


def list_customers(db: Session, shop_id: int) -> list[Customer]:
    return db.query(Customer).filter(Customer.shop_id == shop_id).order_by(Customer.id).all()


def get_customer(db: Session, shop_id: int, customer_id: int) -> Customer:
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.shop_id == shop_id
    ).first()

    if not customer:
        raise LookupError(f"Customer {customer_id} not found")

    return customer


def create_customer(db: Session, shop_id: int, name: str, phone: str | None = None) -> Customer:
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise LookupError("Shop not found")

    if not name or not name.strip():
        raise ValueError("Customer name is required")

    customer = Customer(shop_id=shop_id, name=name.strip(), phone=phone)

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer
