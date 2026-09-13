from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import SaleCreate
from ..services import sales_service

router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)


@router.post("/")
def create_sale(
    sale_data: SaleCreate,
    db: Session = Depends(get_db)
):
    try:
        sale = sales_service.create_sale(
            db,
            sale_data.shop_id,
            items=[item.model_dump() for item in sale_data.items],
            customer_id=sale_data.customer_id,
            payment_method=sale_data.payment_method,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "message": "Sale recorded successfully",
        "sale_id": sale.id,
        "total_amount": sale.total_amount
    }


@router.get("/summary")
def get_sales_summary(
    shop_id: int,
    db: Session = Depends(get_db)
):
    return sales_service.sales_summary(db, shop_id)


@router.get("/")
def get_sales(
    shop_id: int,
    db: Session = Depends(get_db)
):
    sales = sales_service.list_sales(db, shop_id)

    return [
        {
            "id": sale.id,
            "shop_id": sale.shop_id,
            "customer_id": sale.customer_id,
            "total_amount": sale.total_amount,
            "payment_method": sale.payment_method,
            "created_at": sale.created_at,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                }
                for item in sale.items
            ]
        }
        for sale in sales
    ]
