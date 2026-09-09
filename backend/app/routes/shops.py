from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Shop
from ..schemas import ShopCreate, ShopResponse


router = APIRouter(
    prefix="/shops",
    tags=["Shops"]
)


@router.post("/", response_model=ShopResponse)
def create_shop(
    shop_data: ShopCreate,
    db: Session = Depends(get_db)
):
    shop = Shop(**shop_data.model_dump())

    db.add(shop)
    db.commit()
    db.refresh(shop)

    return shop


@router.get("/", response_model=list[ShopResponse])
def get_shops(
    db: Session = Depends(get_db)
):
    return db.query(Shop).all()