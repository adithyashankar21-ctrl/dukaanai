from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CreditTransaction, Customer
from ..schemas import CreditTransactionCreate


router = APIRouter(
    prefix="/credit",
    tags=["Udhaar"]
)


@router.post("/")
def create_credit_transaction(
    transaction_data: CreditTransactionCreate,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == transaction_data.customer_id,
        Customer.shop_id == transaction_data.shop_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    if transaction_data.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Amount must be greater than zero"
        )

    if transaction_data.transaction_type not in ["credit", "payment"]:
        raise HTTPException(
            status_code=400,
            detail="Transaction type must be 'credit' or 'payment'"
        )

    transaction = CreditTransaction(
        shop_id=transaction_data.shop_id,
        customer_id=transaction_data.customer_id,
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        note=transaction_data.note,
        created_at=datetime.now().isoformat()
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return {
        "message": "Credit transaction recorded successfully",
        "transaction_id": transaction.id,
        "customer_id": transaction.customer_id,
        "amount": transaction.amount,
        "transaction_type": transaction.transaction_type
    }
    
@router.get("/balance/{customer_id}")
def get_customer_balance(
    customer_id: int,
    shop_id: int,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.shop_id == shop_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    transactions = db.query(CreditTransaction).filter(
        CreditTransaction.customer_id == customer_id,
        CreditTransaction.shop_id == shop_id
    ).all()

    balance = 0

    for transaction in transactions:
        if transaction.transaction_type == "credit":
            balance += transaction.amount
        elif transaction.transaction_type == "payment":
            balance -= transaction.amount

    return {
        "customer_id": customer_id,
        "customer_name": customer.name,
        "balance": balance
    }