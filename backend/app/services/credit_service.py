from datetime import datetime

from sqlalchemy.orm import Session

from ..models import CreditTransaction, Sale
from . import customer_service

VALID_TRANSACTION_TYPES = ("credit", "payment")


def record_transaction(
    db: Session,
    shop_id: int,
    customer_id: int,
    amount: float,
    transaction_type: str,
    note: str | None = None,
) -> CreditTransaction:
    customer_service.get_customer(db, shop_id, customer_id)

    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    if transaction_type not in VALID_TRANSACTION_TYPES:
        raise ValueError(f"transaction_type must be one of {VALID_TRANSACTION_TYPES}")

    transaction = CreditTransaction(
        shop_id=shop_id,
        customer_id=customer_id,
        amount=amount,
        transaction_type=transaction_type,
        note=note,
        created_at=datetime.now().isoformat(),
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def get_balance(db: Session, shop_id: int, customer_id: int) -> float:
    customer_service.get_customer(db, shop_id, customer_id)

    transactions = db.query(CreditTransaction).filter(
        CreditTransaction.shop_id == shop_id,
        CreditTransaction.customer_id == customer_id,
    ).all()

    balance = 0.0
    for transaction in transactions:
        if transaction.transaction_type == "credit":
            balance += transaction.amount
        else:
            balance -= transaction.amount

    return round(balance, 2)


def list_customer_summaries(db: Session, shop_id: int) -> list[dict]:
    """Every customer (not just those who owe money) with their udhaar
    balance, last payment, and last purchase — the real data behind the
    Udhaar view (amount owed / last payment / last purchase / history)."""
    customers = customer_service.list_customers(db, shop_id)

    transactions = db.query(CreditTransaction).filter(
        CreditTransaction.shop_id == shop_id,
    ).order_by(CreditTransaction.created_at).all()

    sales = db.query(Sale).filter(
        Sale.shop_id == shop_id,
        Sale.customer_id.isnot(None),
    ).order_by(Sale.created_at).all()

    by_customer: dict[int, dict] = {}
    for t in transactions:
        entry = by_customer.setdefault(t.customer_id, {"balance": 0.0, "last_payment": None, "last_credit": None})
        if t.transaction_type == "credit":
            entry["balance"] += t.amount
            entry["last_credit"] = {"amount": t.amount, "created_at": t.created_at, "note": t.note}
        else:
            entry["balance"] -= t.amount
            entry["last_payment"] = {"amount": t.amount, "created_at": t.created_at, "note": t.note}

    last_purchase_by_customer: dict[int, dict] = {}
    for s in sales:
        last_purchase_by_customer[s.customer_id] = {"amount": s.total_amount, "created_at": s.created_at}

    summaries = []
    for customer in customers:
        credit_info = by_customer.get(customer.id, {})
        summaries.append({
            "customer_id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "balance": round(credit_info.get("balance", 0.0), 2),
            "last_payment": credit_info.get("last_payment"),
            "last_credit": credit_info.get("last_credit"),
            "last_purchase": last_purchase_by_customer.get(customer.id),
        })

    summaries.sort(key=lambda r: -r["balance"])
    return summaries


def list_balances(db: Session, shop_id: int) -> list[dict]:
    customers = customer_service.list_customers(db, shop_id)

    results = []
    for customer in customers:
        balance = get_balance(db, shop_id, customer.id)
        if balance > 0:
            results.append({
                "customer_id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "balance": balance,
            })

    results.sort(key=lambda r: -r["balance"])
    return results
