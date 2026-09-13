from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ProductCreate, ProductResponse
from ..services import inventory_service

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.post("/", response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    try:
        return inventory_service.create_product(db, **product_data.model_dump())
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[ProductResponse])
def get_products(
    shop_id: int,
    db: Session = Depends(get_db)
):
    return inventory_service.list_products(db, shop_id)
