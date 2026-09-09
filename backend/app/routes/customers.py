from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Customer
from ..schemas import CustomerCreate, CustomerResponse


router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


@router.post("/", response_model=CustomerResponse)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db)
):
    customer = Customer(**customer_data.model_dump())

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


@router.get("/", response_model=list[CustomerResponse])
def get_customers(
    shop_id: int,
    db: Session = Depends(get_db)
):
    return db.query(Customer).filter(
        Customer.shop_id == shop_id
    ).all()