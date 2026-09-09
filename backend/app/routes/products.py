from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product, Shop
from ..schemas import ProductCreate, ProductResponse


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.post("/", response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    shop = db.query(Shop).filter(
        Shop.id == product_data.shop_id
    ).first()

    if not shop:
        raise HTTPException(
            status_code=404,
            detail="Shop not found"
        )

    product = Product(**product_data.model_dump())

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get("/", response_model=list[ProductResponse])
def get_products(
    shop_id: int,
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(
        Product.shop_id == shop_id
    ).all()

    return products