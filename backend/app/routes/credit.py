from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import CreditTransactionCreate
from ..services import credit_service, customer_service

router = APIRouter(
    prefix="/credit",
    tags=["Udhaar"]
)


@router.post("/")
def create_credit_transaction(
    transaction_data: CreditTransactionCreate,
    db: Session = Depends(get_db)
):
    try:
        transaction = credit_service.record_transaction(
            db,
            transaction_data.shop_id,
            transaction_data.customer_id,
            transaction_data.amount,
            transaction_data.transaction_type,
            transaction_data.note,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "message": "Credit transaction recorded successfully",
        "transaction_id": transaction.id,
        "customer_id": transaction.customer_id,
        "amount": transaction.amount,
        "transaction_type": transaction.transaction_type
    }


@router.get("/balances")
def get_all_balances(
    shop_id: int,
    db: Session = Depends(get_db)
):
    return credit_service.list_balances(db, shop_id)


@router.get("/summaries")
def get_customer_summaries(
    shop_id: int,
    db: Session = Depends(get_db)
):
    """Every customer with balance, last payment and last purchase — the
    Udhaar view's data source."""
    return credit_service.list_customer_summaries(db, shop_id)


@router.get("/balance/{customer_id}")
def get_customer_balance(
    customer_id: int,
    shop_id: int,
    db: Session = Depends(get_db)
):
    try:
        customer = customer_service.get_customer(db, shop_id, customer_id)
        balance = credit_service.get_balance(db, shop_id, customer_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "customer_id": customer_id,
        "customer_name": customer.name,
        "balance": balance
    }
