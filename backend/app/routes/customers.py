from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import CustomerCreate, CustomerResponse
from ..services import customer_service

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


@router.post("/", response_model=CustomerResponse)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db)
):
    try:
        return customer_service.create_customer(
            db,
            customer_data.shop_id,
            customer_data.name,
            customer_data.phone,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search", response_model=list[CustomerResponse])
def search_customers(
    shop_id: int,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return customer_service.search_customers(db, shop_id, q)


@router.get("/", response_model=list[CustomerResponse])
def get_customers(
    shop_id: int,
    db: Session = Depends(get_db)
):
    return customer_service.list_customers(db, shop_id)
